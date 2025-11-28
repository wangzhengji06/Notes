# Podman in action

## 1.2 Command Lines

### 1.2.1 Containers

`podman inspect`

`podman stop -t 0`

-i interative

-d detached

-t terminal

-rm remove when exit

`podman inspect --format '{{ .Config.Cmd }}' myapp` can check the main process

### 1.2.2 Images

`podman commit myapp myimage` to create the image from Containers

`podman image tree myimage` to check the structure of the image

`podman image diff myimage anotherimage` to check the difference

`podman image inspect --format '{{ .Config.Cmd }}' myimage` can check the main process

`podman login quay.io` & `podman push myimage quay.io/lzabry/myimage` to push the image to quay.io

`podman tag myiamge quay.io/lzabry/myimage` to tag the image. BTW, `podman rmi` is doing untag.

`podman search registry.redhat.io/httpd` can search the image when you are not sure.

Here is a cool stuff. Sometimes you want to check the image content without running it as container.
Here are the steps.

1. `podman unshare` enter the user and mount namespace.
2. `mnt=$(podman image mount quay.io/lzabry/myimage)` save the location of the mounted filesystem as an environment variable.
3. ` $mnt/xxx` do whatever you want with this filesystem.
4. `podman image unmount quay.io/lzabry/myimage` unmount it
5. `exit` to quit the shell

### 1.2.3 Building Images

There are two parts of the job. First, you need to add content. FROM, RUN, COPY. Second, you need to tell how to use the container. It includes the following:

1. Entrypoint and CMD: CMD is the actual command to run, and ENTRYPOINT can cause the entire image to execute as a single command.
2. ENV: set up the default environment variables to run when podman run image as a container.
3. EXPOSE: Records the network ports for Podman to expose in containers based on image. Use together with `podman run --publish-all`
