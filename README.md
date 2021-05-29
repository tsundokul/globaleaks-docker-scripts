## GlobaLeaks Docker Scripts

### Usage
Prebuilt up-to-date images are available on [dockerhub](https://hub.docker.com/r/tsundokul/globaleaks)

You can build the image with:
```bash
docker build -t <repo>/globaleaks .
```
Run the built image with:
```bash
docker run --rm -it -p '80:80' -p '443:443' <repo>/globaleaks
```
### With docker-compose (persistent data)
`docker-compose` uses volumes to persist data; build and run with:
```bash
docker-compose up
```
Add `--build` flag to force rebuilding.

Go to http://localhost and follow the setup wizard.

### DockerHub auto-update script
`scripts/image_builder.py` polls the apt repository, checks for updates, rebuilds and publishes the images
```bash
# install required modules
cd scripts
pip install poetry
poetry install

# run the script
export DOCKER_USER=<dockerhub_user>
export DOCKER_PASS=<dockerhub_pass>
(optionally change IMGREPO within the script)
./image_builder.py
```

[@tim17d](https://twitter.com/tim17d)