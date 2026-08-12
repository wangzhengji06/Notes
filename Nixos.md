# Session 1

## Nixos command

`nixos-rebuild repl` What this does is it is going to build the config.build.system.build.toplevel using the xxx as the configuration.nix. But actually you only get the derivation, you dont get the actual thing.

`nixos-rebuild build` will actually build everything, but still wont change the system.

`nixos-rebuild test` will do everything but not have an actual generation.

`NIXOS_CONFIG=xxx sudo -e` is a way to change inline what would be the configuration.nix used to repl, build, test, switch.

`sudo nix-channel --list`

## Nixos Good and Bad

What we want from Nixos is reproducibility. But Nixos by default does not give us that.

1. Configuration.nix is not an actual configuration.nix, it is just NixOS modules. In the implementation, what they just do is instantiate the configuration using configuration.nix. But still, you dont own the configuration itself. Module is like recipe, but not the ingredients.

2. Packages, modules and library are injected into the building process, and we dont like that because these parts are not reproducible.

3. It is related to reason 2, but all those modules, packages and library are coming from a git revision, which ultimately coming from channels. Channel can mutate.

## Flake

A flake is a special nix file that acts as the input locker that replaces the channels. It gives CLI to update the input and overwrite the cli. Another thing here is that it is the entry point for the project. The entry point will always be flake.nix.

But although flake is good for development, but it is not good for consumption. Nixos module should not force the user to use it using flake.

After defining everything, use flake.nix

## Git related

make use of `git add -p`
