# Session with Dawn

## Session 1

### Nixos command

`nixos-rebuild repl` What this does is it is going to build the config.build.system.build.toplevel using the xxx as the configuration.nix. But actually you only get the derivation, you dont get the actual thing.

`nixos-rebuild build` will actually build everything, but still wont change the system.

`nixos-rebuild test` will do everything but not have an actual generation.

`NIXOS_CONFIG=xxx sudo -e` is a way to change inline what would be the configuration.nix used to repl, build, test, switch.

`sudo nix-channel --list`

### Nixos Good and Bad

What we want from Nixos is reproducibility. But Nixos by default does not give us that.

1. Configuration.nix is not an actual configuration.nix, it is just NixOS modules. In the implementation, what they just do is instantiate the configuration using configuration.nix. But still, you dont own the configuration itself. Module is like recipe, but not the ingredients.

2. Packages, modules and library are injected into the building process, and we dont like that because these parts are not reproducible.

3. It is related to reason 2, but all those modules, packages and library are coming from a git revision, which ultimately coming from channels. Channel can mutate.

### Flake

A flake is a special nix file that acts as the input locker that replaces the channels. It gives CLI to update the input and overwrite the cli. Another thing here is that it is the entry point for the project. The entry point will always be flake.nix.

But although flake is good for development, but it is not good for consumption. Nixos module should not force the user to use it using flake.

After defining everything, use flake.nix

### Git related

make use of `git add -p`

## Session 2

### Make the output of flake the instantiation of the configuration

cli can take any attrpath of the output of the flake. You can use whatever the form you like, but usually people like to do `nixosConiguration.hostname` because it is expected. 

The result of the flake will be a `nixosConfiguration`.

flake by default uses pure mode. This means that, only the file that git is aware of can be copied into the nix store. So, only abosluate nix store path and relative path can be used.

`nix flake metadata` is a good command that can be used to check the flake.

There are different ways to fetch the nixpkgs, like tarball...

What does `flake=false` do? it means only fetching the input, while true would fectch the input and also evaluate its flake.

Inside `flake.lock`, the hash stands for the content that is fetched. When flake redownloads something, it needs to make sure the input is the same.

`nixos-rebuild build --flake .#golden` is used to build the system.

flake is pure, so cannot use something like `builtin.currentSystem` etc....

A good part about flake is you get the evaluation cache. You also control the source.

### Git worktree and bare repo
A bare repo means that you only get the .git file. Worktree is a seperate directory where one branch is checked out, while still sharing the same .git.
Here a useful alias is `clone --bare --config remote.origin.fetch=+refs/heads/*:refs/remotes/origin/*` 


### Nixos module system
The modules attr name, can accept function / attrset, or string like patterns. The reason why we directly pass the path string to module list is because, it allows to generate a key that is  to avoid deduplicate the module import.

After I evaluate the configuration.nix, the NixOS module system loads it, calls it with module arguments like config, lib, and pkgs, and gets back a module attrset, I got to see that it returns a attrset. Then attrset is evaluated using the lib.evalModules.

It contains type, class, bascially telling you that "I am the configuration of nixos". config is the value of the options, it is also the result of evaluation. pkgs is the instance of the nix packages used here.

### Why is my build different than your build?
You should use `https://releases.nixos.org/nixos/unstable/.../nixexprs.tar.xz` as a fact that tarball is very explicitly just the Nixpkgs source tree. This will give you teh same source as the nix way of building the system


# Session from Online Video

## Introudction

### Inject and Run

`nix run nixpkgs#hello` does just a simple run. For example, `nix run nixpkgs#ripgrep -- --version` here the first `--` is used purely as a seperator.

`nix shell nixpkgs#hello` create an actual shell session.

`nix-shell -p hello ripgrep` is a good way to include mutiple packages into one shell.

### Expose Systemwide bin

`nix profile` is a way to remove or add packages and expose them systemwise. For example, `nix profile list` will list all the current packages. `nix profile add nixpkgs#ripgrep` will add the ripgrep into the profile.

What nix profile does is, it will append all these bin files to ~/.nix-profile/bin/. You can of course remove it using `nix profile remove nixpkgs#ripgre`.

You can even use `nix profile rollback` if you did some unwanted changes. Why is this possible? Becuase nix stores all the generations in the `.local` folder, and each generation is just a symlink.

`nix profile upgrade --all` will update all the packages inside nix profile.

### Clean(pinned also)

`nix-collect-garbage` will automatically clean all the unpinned files in nixstore. However, for example, our nix-profiles still have a backup for all the previous versions. To install these files as well, use `nix-collect-garbage -d`.

## Nix as a language

`nix eval --json` allows you to render the nix version to json. File format like `json`, `yaml`, `toml` are all supported, so you can use nix as the template.

Now everything below assumes that you are typing insdie a nix repl.

`:doc builtins.throw` allow you to see the help command from nix on how to use this function.

`nix repl --file '<nixpkgs>'` eval Nix expression interactively against Nixpkgs.

`:u pkgs.hello` built it + give me a shell where I can use it.

`:b pkgs.hello` Build it.

`:p {x=1; inherit s;}` means print the value recursively.

`:r` to reset.

### attrset and inherit

`{}` works like a dictinoary in python

`{inherit x; inherit (s) a b; }` here it bascially means take the s.a and s.b into the a and b inside this attrset.

`set ? a` is a in the attrset?

`set.c or 10` is set.c there? if not give me 10.

You can think of currying in nix like Python's class.

`let` is good because after the let cluase ended it goes out of the scope.

`with` will overwrite the previous with, if two with in the same scope. But global one always wins.

Use two \`\` to start margical lines.

You can use `//` to do union. Union, just like with, will let the latter one wins.

`import file.nix` is just trying to evaluate the nix pression in file.nix.

There is no statement in nix, the whole file has to be one big expression.

### How to debug the nix

You can use `builtins.trace "hello!" (x+y+z)` to print some helpful information

`break` written inside nix will set a breakpoint, you can use `nix eval -f debug.nix --debugger` to stop at the break point, and use `:env` to check the variables, and use `:c` to continue.

### Lazy Evaluation

Nix ix doing lazy evaluation. Which means: it sometimes wont access the variable, if all it needs is to evaluate its length, or even no need for evaluation at all. o

### List

has `tail`, `head`, `length`.

Use `++` to conctenate list.

Plese always add space `x + 1`, because nix allows the name like `x-1` as a variable name.

### map, filter, foldl' and friends

`builtins.filter (x: x > 2) [ 100 2 30 ]` can be used to filter

`map (x: x * x) [ 1 2 3 4 5]` can be used to map

`foldl` just like reduce

### Way to import Nixpkgs

`pkgs = import ./path/to/nixpkgs {}` the nixpkgs actually return a function, thus it is required to provide an empty bracket, or some real arguments.

## Dev Shell

### The normal way: using nix-build and nix-shell

The problem with docker is that, first, it seperates the environment, also every time you want to make change you will have to rebuild docker.

Here is an example of shell.nix that you can define

```nix
let
  pkgs = import <nixpkgs> { };
in

pkgs.mkShell {
  packages = with pkgs; [
    byacc
    automake
    autoconf
    pkg-config
    gnumake
    ncurses
    libevent
  ];
}
```

You can use this to build tmux. What is better compared to docker is that, when you want to rebuld the tool using bison instead of byacc, you can just redownload package, and rebuild, But if you are using docker, then you will have to rebuild everything again.

Now you can smoothly transform from shell.nix to default.nix

```nix
let
  pkgs = import <nixpkgs> { };
in
pkgs.stdenv.mkDerivation {
  name = "tmux";
  src = ./.;

  nativeBuildInputs = with pkgs; [
    byacc
    automake
    autoconf
    pkg-config
  ];

  buildInputs = with pkgs; [
    ncurses
    libevent
  ];
  preConfigure = ''
    ./autogen.sh
  '';
}
```

`nativeBuildInputs` are all the commands that you really use during the build process.

And here is a even more beautiful thing, if you use `nix-shell`, and there is not `shell.nix`, it will actually read `default.nix`, and install all those nativeBuildInputs and buildInputs.

So now we both have a development shell and a production deployment method.

We can also write the following release.nix

```nix
let
  pkgs = import <nixpkgs> { };
  tmux = pkgs.stdenv.mkDerivation {
    name = "tmux";
    src = ./.;

    nativeBuildInputs = with pkgs; [
      byacc
      automake
      autoconf
      pkg-config
    ];

    buildInputs = with pkgs; [
      ncurses
      libevent
    ];
    preConfigure = ''
      ./autogen.sh
    '';
  };

in
{
  inherit tmux;
  devShell = pkgs.mkShell {
    packages = with pkgs; [
      shellcheck
      clang-analyzer
    ];
    inputsFrom = [ tmux ];
  };
}

```

Then we can use `nix-build release.nix -A tmux` to build the nix from the attribute set returned.

We can further define the shell.nix as the following

```nix
(import ./release.nix).devShell
```

And your default.nix can be

```nix
(import ./release.nix).tmux
```

We get the both of best worlds, we get a minium deployment way, and we can also have a development environment with tools installed.

### The flake way

Use `nix flake init` to initiate a directory, it will create `flake.nix` with tempaltes inside.

We can make use of the release.nix to do the magic trick

```nix
{
  description = "Cool tmux flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
    in
    {
      packages.x86_64-linux.default = pkgs.stdenv.mkDerivation {
        name = "tmux";
        src = ./.;

        nativeBuildInputs = with pkgs; [
          byacc
          automake
          autoconf
          pkg-config
        ];

        buildInputs = with pkgs; [
          ncurses
          libevent
        ];

        preConfigure = ''
          ./autogen.sh
        '';
      };
    };
}
```

Also by making use of `nix build -L` we can show the full log of what is being built.

Also use `nix flake show` to evaluate the flake, what will be built in the end?

Use `nix develop` to enter into the development shell defined by flake.

### direnv

Just use it....
