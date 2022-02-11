#!/usr/bin/env python

import docker
import logging
import os
from apt_repo import APTSources, APTRepository
from packaging import version
from time import sleep

IMGREPO = 'tsundokul/globaleaks'
APTREPO = ('http://deb.globaleaks.org', 'bullseye')
WAIT = 10 * 60

def make_client():
  """Creates a docker client. Uses environment vars
      DOCKER_USER and DOCKER_PASS to log in
  Returns:
  docker.client.DockerClient: authenticated client
  """
  client = docker.from_env()
  client.login(
    os.environ['DOCKER_USER'],
    os.environ['DOCKER_PASS'])
  return client

def get_latest_image_version(client, img_name):
  """Retrieves all tags of an image, and parses the versions
  Returns:
  packaging.version.Version: highest version
  """
  try:
    tags = client.images.get(img_name).tags
    tags = [t for t in tags if t[-1].isnumeric()]
    tags = [version.parse(t.split(':')[-1]) for t in tags]
  except docker.errors.ImageNotFound:
    tags = (version.parse('0.0.0'), )

  return max(tags)

def get_latest_repo_version(repo, package='globaleaks'):
  """Retrieves all globaleaks package versions from an apt repository
  Returns:
  packaging.version.Version: highest version
  """
  sources = APTSources([APTRepository(*repo)])
  versions = [p.version for p in sources.get_packages_by_name(package)]
  versions = [version.parse(v) for v in versions]
  return max(versions)

def build_globaleaks_img(client, version, repo, path='..'):
  """Builds and tags an image
  Returns:
  list: built image tags
  """
  img, _logs = client.images.build(path=path, nocache=True, pull=True, rm=True)
  tags = (str(version), f'{version}-bullseye', 'latest')

  for tag in tags:
    img.tag(repo, tag)

  return tags

def push_tags(client, repo, tags):
  """Pushes to dockerhub specific tags of an image
  """
  for tag in tags:
    client.images.push(repo, tag)

def test_image(docker_client, image, expected_version):
  out = docker_client.containers.run(
    image=f'{image}:{expected_version}',
    entrypoint='globaleaks',
    command='-v',
    detach=False,
    remove=True
  ).decode()

  assert str(expected_version) in out, f'Version mismatch: {expected_version} / {out}'


if __name__ == '__main__':
  logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO)
  logging.info('Logging in...')
  client = make_client()

  image_ver = get_latest_image_version(client, IMGREPO)

  while True:
    try:
      repo_ver = get_latest_repo_version(APTREPO)
    except AttributeError:
      print("Repo error, skipping this try")
      sleep(WAIT)
      continue

    if repo_ver > image_ver:
      logging.info(f'Versions: {image_ver} (image), {repo_ver} (repo)')
      logging.info(f'Updating image...')

      try:
        tags = build_globaleaks_img(client, repo_ver, IMGREPO)
        test_image(client, IMGREPO, repo_ver)
   
        logging.info(f'Pushing tags: {tags}')
        push_tags(client, IMGREPO, tags)

        image_ver = repo_ver
        logging.info(f'Update finished')

      except docker.errors.BuildError as e:
        # Sometimes new packages are not signed and the build may fail
        # for this specific scenario, wait for 3x the ammount of time
        logging.error(e)
        sleep(WAIT*2)

    sleep(WAIT)
