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

| Container UID | Host UID | Range |
| ------------- | -------- | ----- |
| 0             | 1000     | 1     |
| 1             | 100000   | 65536 |

This is my mapping result. To allow user id `60` inside container to be able to write to http, I can do `podman unshare chown 60:60 ./html`
This will change the ownership to 10059 on host, but it allows the podman to write to it.

This is exactly the use of `-U` does. For example, mariadb runs with user mysql with id 999. We can do this.
`podman run --user mysql -v ./mariadb:/var/lib/mariadb:U  docker.io/mariadb ls -ld /var/lib/mariadb`
Here, the U tells the podman to recursively change the ownership for the source file to match the default UID.
If you check the ownership on host, you will find that now the folder belongs to 10098.

`z` and `Z` are used to recursively change the security of labels on the host to allow containers to manipulate them.
However, this of course brings risk. If the files will only be used by containers, of course it is okay.
But, using this option on a home directory can have disastrous effects on the system because it recursively relabels all content in the directory as if the data was private to a container.
Other confined domains would be prevented from using the mislabeled data.
For these cases, you need `podman run --security-opt label=disable -v /home/lzabry:/home/lzabry -p 8080:8080 quay.io/lzabry/myimage`

Another very useful option would be `:O`, this is super useful if you want the host to be unchanged while using container to freely read and write.

### 1.3.3 podman run --mount command option

`podman run --mount` works the same as `pdoman run -v`, and it is more explicit.
In most of the cases, the container image should be read only,and any data that needs to be written should be stored outside of images via volume.

## 1.4 Pods

Pod is a group of one or more containers working together for a common purpose and sharing the same namespace and cgroups. Also podman ensure that all container processed within a pod share the same SELinux labels.

### 1.4.1 Running Pods

Podman pods always contain a container called infra, which hold open the namespaces and cgroups. It has a container monitor process called conmon that will monitor it.
Podamn allows for init container, than can run the first time pods is created, or run everytime pod is started. With the init container completed, podman starts the primary containers. Here podman allows sidecar containers to monitor the primary container. The number of sidecar containers can be 0 or more.

The biggest advantage of running pods: you start the pod, every containers inside it start. You stop the pod, every containers inside it stop.

### 1.4.2 Creating a pod

`podman pod create -p 8080:8080 --name mypod --volume ./html:/var/www/html:z` to create a pod named mypod using `podman pod create` command.
Notice that, here the port is binds 8080 to 8080, and the volume is mounted, this is done for every containers inside the pod.

### 1.4.3 Adding containers to pod

`podman create --pod mypod --name myapp quay.io/lzabry/myimage` to create a main container.
`podman create --pod mypod --name time --workdir /var/www/html ubi8 ./time.sh` to create a sidecar container. Here the workdir set the location in container and the time.sh will run from this location as `/var/www/html/time.sh`

Here what happens is, the podman mounts the /html on local host to /var/www/html inisdei container. So inside the second container, the time.sh could be found.

### 1.4.4 Starting a pod

`podman pod start mypod` to start the pod.

### 1.4.5 Stopping a pod

`podman pod stop mypod` to stop the pod.

### 1.4.6 List the pod

`podman pod list` to list pods.

### 1.4.7 Removing pods

`podman ps --all --format "{{.ID}} {{.Image}} {{.Pod}}"` to check the containers.
`podman pod rm` ro remove pod.
