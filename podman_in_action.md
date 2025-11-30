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

## 1.3 Volumes

podman allows you to mount the host filesystem content into containers using `podman run` and `-v`

For exapmle, you can do this ` podman run -d -v ./html:/var/www/html:ro,z -p 8080:8080 quay.io/rhatdan/myimage`
Here, the `ro` means Podman should mount the volume in read-only mode. `z` is for SELinux which would be exaplined later.

### 1.3.1 Named Volumes

Another mechanism is called volume. You can create using `podman volume create`
For example, `podman volume create webdata`. If you use `podman volume inspect webdata` to check the named volume, you will find that the volume is inside local host.
`cat > /home/lzabry/.local/share/containers/storage/volumes/web-data/_data/index.html << _EOL` can be used to manipulate on volume.
`podman run -d -v webdata:/var/www/html:ro,z -p 8080:8080 quay.io/lzabry/myimage` can be then used to run the container using named volume.
Just like the bind volume, named volume can also be used by multiple containers at the same time.

`podman volume rm --force webdate` to remove the named volume as welll as the container.

`podman volume list` to list all the named volume.

If a volume has not been created before the podman run comamnd, it will be created automatically.

### 1.3.2 Volume mount options

`ro` tells Podman to mount the read-only volume, `z` tells Podman to relabel the content with SELinux labels that allow multiple containers to read and write in the volume.
Consider the scenario of mounting a html directory on host.
The html directory is owned by your host UID (1000).
Inside a rootless containerm the container processes cannot write to it unless they run as a user whose container-UID maps to host UID 1000.

`podman unshare cat /proc/self/uid_map` can shows the mapping ip for it.

| 0 | 1000 | 1 |
| 1 | 100000 | 65536|

This is my mapping result
