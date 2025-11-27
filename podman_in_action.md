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
