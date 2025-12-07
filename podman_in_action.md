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

## 2.1 Customization and configuration files

Podman has a lot of configuration files for you to change the default behaviour.

### 2.1.1 Configuration files for storage

`sudo podman info` and `podman info` will show the images storage information for rootless and rootful contaners.

To change the default storage place, use `/etc/containers/storage.conf`

By default, the podman uses overlay as the storage driver, which is the overlay2 in docker.
You might want to change the overlay driver from FUSE(default one)

### 2.1.2 Configuration files for registries

Check `/etc/containers/registries.conf`, the setting you want to tweak is unqalified-search-registries, you can change the default public registires it is used to pull images from.
Another interesting thing you can do is to block users from pulling from certain registries.
For example,

```
[[registry]]
Location = "docker.io"
blocked=true
```

By this, you block the users from pulling from docker.io.

Also, if one of your users is working without internet, and you want to provide a mirror registry to let them pull, you can do this:

```
[[registry]]
location="registry.access.redhat.com"
[[registry.mirror]]
location="mirror-1.com"
```

### 2.1.3 Configuration files for engines

You can have multiple .conf files that define the env the container should be run with.
`podman run --rm ubi8 printenv`

How to change these env variables? Do this:

```
mkdir -p $HOME/.config/containers/containers.conf.d
cat << _EOF > $HOME/.config/containers/containers.conf.d/env.conf
[containers]
env=[ "foo=bar" ]
_EOF
```

Here the author used a very complex example of running podman itself inside a container, because inside the container many env does not work, here the author modify the .conf file so that, the container can access to the host service.

### 2.1.4 System Configuration files

`/etc/subuid` and `/etc/subgid` files define the mapping of namespace. Podman reads them to assign uid, so pretty important.

## 2.2 Rootless Containers

The problem with docker is that, even if the docker-client can be run as non-root, it connects to a root running daemon, giving full root access to the host OS.

### 2.2.1 How does rootless Podman work?

Let's first run a rootless container as an example, do `podman run -d -p 8080:8080 --name myapp quay.io/lzabry/myimage`

#### 2.2.1.1 Images contain content owned by multiple user identifiers(UIDs)

In Linux, UID and GID are assigned to process and stored on filesystem objects. This access is called discretionary access contol(DAC).

`podman run --user=root --rm quay.io/lzabry/myimage -- bash -c "find / -mount -printf \"%U=%u\n\" | sort -un" 2>/dev/null` Let's run the container as root to examine every file within the image.

You will see that there are 4 uids inside container:

```
0=root
48=apache
1001=default
65534=nobody
```

Because linux does not allow files to be created by multiple users, you will have to get creative with the userids you have.

To check the uid mapping, you can do `cat /etc/subuid`

On my pc, it shows `lzabry:100000:65536`. This means that lzabry as a user can have `100000 to 165536` for its assigned user id in namespace.
Why starts at 100000? Because Linux allows you to have around 99000 regular users, and 1000 UIDs reserved for system service.

Every process on a Linux Namespace is in a user namespace. `cat /proc/self/uid_map` will show `0     0 4294967295`, which basically means, 0 -> 0, 1 -> 1, ......

In host namespace, there is no real mapping.

We can now enter into user namespace. Podman has a special command called `podman unshare`, which allows you to enter a user namespace without launching a container.

Let's do this command again using `podman unsahre cat /proc/self/uid_map`, you will see `0       10000 1  1       100000 65536`

This shows that UID 0 is mapped to UID 1000(my uid) for a range of 1, and UID 1 is mapped to 100000 for a range of 65536.

Any UID not mapped to the user namespace is reported within the user-namespace as nobody user. you can confirm by `podman unshare ls -ld /`

And user cannot actually make change to file created by `nobody` unless the `other` rule allows for it.

`podman unshare bash -c "id ; ls -l /etc/passwd; grep lzabry /etc/passwd; touch /etc/passwd"`, you will see that /etc/passwd is world reable, but you cannot make change to it.

`podman unshare bash -c "mkdir test;touch test/testfile; chown -R 1:1 test"`, this will create a file that is owned by 100000 on host, and if you want to delete it on host you cannot, because outside the user namespace, you have access to only your UID, you don't have access to the additional UIDs.

This looks weird because inside container I am actually root, and I cannot rmove something? That is because on linux, the root processes actually is powerful with Linux capabilites, and without it, it is not that powerful.

Besides userspace, whether you can mount a file is actually also determined by mount namespace. The mount points are not seen by the process outside the mount namespace.
For example, `echo hello > /tmp/testfile` and `mount --bind /tmp/testfile /etc/shadow` will give you an error saying only root can do that. But `podman unshare bash -c "mount -o bind /tmp/testfile /etc/shadow; cat /etc/shadow"` will succeed. Once you exit, everything return to normal.

### 2.2.2 Rootless Podman under the covers

Now let's understand what happesn what Podman does when it runs a container.

1. Podman first read `/etc/subuid` and `/etc/subgid` files, looking for the username and UID. Once the Podman finds the entry, it generates a user namespace for you, Podman than launches the podman pause process to hold open the user and mount namespace.

2. Podman pull the images. It will check if the image exists in local container storage. If not, it will pull using containers/image library. After all the layers are assemebled and untarred, containers chowns the UID/GIDs of files into home directory.

3. Podman creates the container. It creates a new container entry in its database, and asks the storage library to make a writable layer for the container, use overlayfs to stack this writable layer.

4. Podman set up the network by using slirp4netns to configure the host network and simulate a VPN for the container.

5. Starting the container monitor, conmon.

6. Launch the OCI runtime. It includes set up additional namespaces, configure cgroups2, set up the SELinux label .... and conmon reports the success back to Podman

7. podman stop. The kernel sends a SIGCHLD to the conmon process.

## 3.1 Integration with systemd

A way to share the containerized service with the world is using systemd.

### 3.1.1 Running systemd within a container

Microservice is defined as one specialized service within a container. This single service runs as the initial PID within the containers and writes its log directly to `stdout` and `stderr`. Kubernetes assumes this way. Another school of thought would run several services inside one container.

A huge advantage of the latter is, microservice run the service using PID 1, but if you run multiple processes inside a container, the zombie process can be killed(`podman run -init`)

`podman pull ubi8-init` and `podman inspect ubi8-init --format '{{ .Config.Cmd }}'`, you will find the output is `/sbin/init`, this shows that the image is trying to run as a systemd process.

#### 3.1.1.1 Containerzied systemd requirements

Systemd needs some requirements to be met for running within a rootless container.

1. /run on tmpfs
2. /tmp on tmpfs
3. /var/log/journald on tmpfs
4. ENV: container exists
5. STOPSIGNAL=SIGTMIN + 3

#### 3.1.1.2 Podman container in systemd mode

`podman create --rm --name SystemD -it --systemd=always ubi8-init sh` here, `--systemd=always` means runs the container in systemd mode even when not running systemd.
`podman inspect SystemD --format '{{ .Config.StopSignal}}'` will show SIGRTMIN + 3.
`podman start --attach SystemD` to start the container.
`mount | grep -e /tmp -e /run | head -2` show the mount information related to the first two lines about /tmp and /run.
`printenv container` will return Oci.

Notice that the above commands use `sh` to overide the command which casues `/sbin/sh` to be overwritten as an entry point. We will run again.

`podman run -ti ubi8-init` will start the systemd inside the container. systemd would ignore SIGTERM by pressing `CTRL + C`. You need to do `podman stop l` in different terminal.

#### 3.1.1.3 Running an Apache service within a systemd container

```
FROM ubi8-init
RUN dnf -y install httpd; dnf -y clean all
RUN systemctl enable httpd.service
```

Now this will run httpd service at the start of the container.

`podman build -t my-systemd .` and `podman run -d --rm -p 8080:80 -v ./html:/var/www/html:Z my-systemd`, now you should see the HTTPD service being started like it is inside a vm`podman logs xx` you will find there is no output, because pid=1 is systemd, if you need to check log, you need to exec inside the container to read the httpd logs.

### 3.1.2 journald for logging and events

#### 3.1.2.1 Log Driver

There are several log driver options, including Journald, k8s-file. Journald persist logs after container removal, and also supports log rotation.
You can check the default log driver on system by `podman info --format '{{ .Host.LogDriver }}'`

If it is not journald, you can do:

```
mkdir -p $HOME/.config/containers/containers.conf.d

cat > $HOME/.config/containers/containers.conf.d/log_driver.conf << _EOF
[containers]
log_driver="journald"
_EOF
```

Next, run this `podman run --rm --name test2 ubi8 echo "Check if logs persist"`
and `journalctl -b | grep "Check if logs persist"` will show that indeed it records the journal for podman.

#### 3.1.2.2 Events

Log driver records what happens inside container, and events log records lifecycle of the container.
`podman info --format '{{ .Host.EventLogger }}'` to check the event logger.
`podman events --filter event=start --since 1h` You can see the start event of the last container you ran.
