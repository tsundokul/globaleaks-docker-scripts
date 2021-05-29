#!/usr/bin/env python

import docker
import logging
import os
from apt_repo import APTSources, APTRepository
from packaging import version
from time import sleep

IMGREPO = 'tsundokul/globaleaks'
APTREPO = ('http://deb.globaleaks.org', 'buster')
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
  tags = client.images.get(img_name).tags
  tags = [t for t in tags if t[-1].isnumeric()]
  tags = [version.parse(t.split(':')[-1]) for t in tags]
  return max(tags)

def get_latest_repo_version(repo, package='globaleaks'):
  """Retrieves all globaleaks package versions from an apt repository
  Returns:
  packaging.version.Version: highest version
  """
  sources = APTSources([APTRepository(*repo)])
  versions = [p.version for p in sources.get_packages_by_name('globaleaks')]
  versions = [version.parse(v) for v in versions]
  return max(versions)

def build_globaleaks_img(version, repo, path='..'):
  img, _logs = client.images.build(path=path)
  tags = (str(version), f'{version}-buster', 'latest')

  for tag in tags:
    img.tag(repo, tag)

  return tags

def push_tags(client, repo, tags):
  for tag in tags:
    client.images.push(repo, tag)

if __name__ == '__main__':
  logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO)
  logging.info('Logging in...')
  client = make_client()

  try:
    image_ver = get_latest_image_version(client, IMGREPO)
  except docker.errors.ImageNotFound:
    image_ver = version.parse('0.0.0')

  while True:
    repo_ver = get_latest_repo_version(APTREPO)

    if repo_ver > image_ver:
      logging.info(f'Versions: {image_ver} (image), {repo_ver} (repo)')
      logging.info(f'Updating image...')

      tags = build_globaleaks_img(repo_ver, IMGREPO)
      logging.info(f'Pushing tags: {tags}')
      push_tags(client, IMGREPO, tags)

      image_ver = repo_ver
      logging.info(f'Update finished')

    sleep(WAIT)
