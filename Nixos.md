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

The modules attr name, can accept function / attrset, or string like patterns. The reason why we directly pass the path string to module list is because, it allows to generate a key that is to avoid deduplicate the module import.

After I evaluate the configuration.nix, the NixOS module system loads it, calls it with module arguments like config, lib, and pkgs, and gets back a module attrset, I got to see that it returns a attrset. Then attrset is evaluated using the lib.evalModules.

It contains type, class, bascially telling you that "I am the configuration of nixos". config is the value of the options, it is also the result of evaluation. pkgs is the instance of the nix packages used here.

### Why is my build different than your build?

You should use `https://releases.nixos.org/nixos/unstable/.../nixexprs.tar.xz` as a fact that tarball is very explicitly just the Nixpkgs source tree. This will give you teh same source as the nix way of building the system

## Session 3

Why should you use nixos-rebuild build/boot? Because you technically cannot really switch a running kernel.

Question: I am only updating the nixpkgs by a small version, why does it download 4GB of data?

Answer: it is all the renewed build recipe,(like commit etc, not really derivation though) when you are doing flake uipdate, and nix does not patch your system. it is more likely completely copy something into the nixstore.

`nh os test .#golden` build and acitvate the new configuration

What does <pkgs> refer to? it refers to `nixosConfiguration.host.pkgs`. Also, `nixosConfiguration.host.config.nixpkgs.pkgs` is supposed to be an empty attribute set unless we provide one.

Strage thing we met, command not found is not available. THe reason is that we are using a very new channel that is not a release branch.

`nh os build-vm -r .` will be my new friend everytime I made change to the config.

One thing about the vm, it sets a weird default password.

```nix
virtualisation.vmVariant = {
	users.users.lzabry.initialPassword="";
};
```

`inherit (person) name age;` is equla to `name = person.name; age = person.age;`

## Session 4

### Options and Config
Check the home-manager/modules/nushell.nix. It will show you the module can declare options and provide config as the value.

### Homemanager
Nixos and homemanager does not share the same modules. Home manager has more user-related programs.

It is more convenient to use homemanager in a NixOS module instead of using the `evalxxx`, if you are on nixos.

The homemanager import the nixos module which injects the `homemanager.users` options, and we can provide the value for that option. 

We are basically providing a a Home Manager module function.

In the configuration.nix, I need to refer to a package I enabled in home manager. I can use `config.home-manager.users.lzabry.programs.nushell.package`; 

### Git Workflow

After creating a new file using `git add -N`, you can view change `git diff`.

But suppose that you want to stash those changes, what to do? `git reset` unstage files but kept the change.

Then you can do your `git stash push -u`. this will allow you to stash the newly added file also.

You can use `git clean -i`  to remove stuff also.
 
`git stash push -p` what hunk should go inside. This is really good before you are trying to make commit.

`git commit --amend -m "qemu virtio-vga-gl"` allows us to change the last commit message and recommit

`git restore -p` allow you to choose what hunk to recover.

Confusing parts: 
The beginning is that we met an error in home.nix but we do not have diagnostic inline.
So we modified the nixvim.nix to make it has that function.
Then,
1. I did nh os test using the new nixvim config.
2. We accidentally? git stash pop everything, which inlcudes home.nix as well as configuration.nix.
3. So we use git stash push -p and restash the neovim. Then we actually test to see how neovim is working after the nixvim config change.
4. It actually works, but teh weird thing is some count number is not rendered. so we use git stash push -u
5. Then we do a git stash list, and pop the stash at 1. And check the neovim config again.
6. We decide to give up and think this version is good enough. We do git add . and commit.

### The most tricky part -> make nixvim a standalone flake output
I want `packages.x86_64-linux.pug` to be a package. And since I am directly defining it as `(import ./nixvim.nix inputs).config.build.package`, then `nixvim.nix` 's output is just the built package.

Very confusingly, I need to somehow include the nixvim package in my user home right? I can add to packages as `inputs.self.packages.x86_64-linux.pug`. What is going on here? flake exposes the output through `inputs.self`, here the flake.nix already uses inputs, so configuration.nix also has inputs. 

We dont want the imported things as a binding, we want a direct built packages using `evalNixvim`


### Others
Currently I have met Nixos Module, Nixvim Module, Homemanager module would also be a different kind of module.
They all use wrapper of lib.evalModules, using something like `evalNixos`, `evalNixvim` etc..

There are two kinds of fetchers. `builtins.fetchTarball` will return a nixstore path that contains the source file. On the other hand, `fetchfromGithub` will return a derivation.


Avoid build from derivation pattern: Something from a realization, occured during evaluation, is used again in that derivation. This is known as the inehrit from derivation pattern.


### Homeworks

1. Get familiar with the keybinding for daignostic 
2. Understand why does count not work
3. Start a pull request for the home manager
4. Read the dedentric pattern.



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

## How Nix builds: sandbox -> derivation -> hash -> store

- Evaluations translate .nix expressions to .drv derivations
- A derivation is a machine-readable recipe without dynamic types
- A realized derivation results in a read-only output path with build products: /nix/store/<hash>-<packagename>

The hash for build products, unlike docker, describes the input.

### Inside the sandbox

Suppose we have builder.sh as the following

```bash
echo "hello there" > $out
```

And we have the default.sh as the following

```nix
let
  pkgs = import <nixpkgs> { };
in
derivation {
  name = "myDerivation";
  system = builtins.currentSystem;

  builder = "${pkgs.bash}/bin/bash";
  args = [ ./builder.sh ];

}
```

If you type `echo ${nix-build}` you will see the message "hello there", this should be expected.

`builtins.derivation` is the most fundemental function used to build drv. It has 4 parameters, name is just used as the name. system is just a tag of what this package is meant to be built on. builder here is spcified to bash because we need something to run the build command, and args can be a lot of commands to be executed inside the bash.

The whole build process happens inside a sandbox. If you want to specify any env, you can add it inside derivation.

Now look at this setup

```nix
let
  pkgs = import <nixpkgs> { };
in
derivation {
  name = "minimal-package";
  system = builtins.currentSystem;

  builder = "${pkgs.bash}/bin/bash";
  args = [ ./builder.sh ];

  COREUTILS = pkgs.coreutils;

}
```

```bash
declare -x

echo "we are in $PWD"
$COREUTILS/bin/ls -lsa

echo "hello there" > $out

```

What would happen is nix saw that you are using a drv inside the input, so it will build it and put it in the Nixstore. The whole coreutils will be realized.

It is not surprising that the `ls` basically prints nothing.

A better way of using ls is:

```nix
PATH = "${pkgs.coreutils}/bin";
```

To summarize, sandbox is basically purely detached from our environment, we cannot access any files or download from internet, we only have minimal POSIX environment.

Also a trick to add some tool inside sandbox is using the following

```nix
PATH = pkgs.lib.makeBinPath [
	pkgs.coreutils
	pkgs.curl
	pkgs.input
];
```

### What is derivation

`nix derivation show $(nix-instantiate  )` We can use this to showe that what drv is created.

Here the `nix-instantiate` means it only creates the drv, not build it fully.

### runtime dependencies

By checking `ldd ./bin/xxx` we can see that the binary depends on some run-time environment. So if we directly copy this to another server without the run time environment, it would fail.

`nix-store --query --tree $(nix-build)` allows you to check the run time dependencies

`nix-store --query --tree $(nix-instantiate)` allows you to check the compile time dependencies

When closing down the sandbox, nix evaluates the hash and the original hash, and understand what are run-time dependencies. so Nix builds a closure for that program.

You can also use `nix-tree` which bascially shows everything in a more clear way.

Another good command is `nix-diff` to check how two dependency trees are different.

To copy closure: `nix copy --to ssh://server $(nix-build ...)`

`nix why-depends ./result /nix/store/...-glibc-...` tells you why ./result depends on this dependency
[112;5u

### bad surprise

Make a src folder if you can, otherwise you might copy something you dont want into sandbox.

A trap is copying the result file into the sandbox, now you have different has and no cache everything you rebuild....

## Package software with stdenv.mkDerivation

`stdenv.mkDerivation` is built on top of `builtins.derivation`. This is the method that we usually acutally use...

Usually when you build an open source project from source, you first wget the tar.gz file, then you use tar xf to unzip it. Then you run `./configure`, `make`, `make test`, `make install` to install the software on your system.

```nix
let
  pkgs = import <nixpkgs> { };
in
pkgs.stdenv.mkDerivation {
  name = "hello";
  source = "./.";
}
```

### What is behind stdenv.mkDerivation

This whole process can be seen as magical, as we do not have gnumake, and if we dont archive it, it will still work, which means it automatically use `tar xf`.

The stdenv comes with the following dependencies by itself:

- Bash
- C compiler
- coreutils
- findutils
- diffutils, patch
- patchelf
- awk grep sed
- tar bzip2 gzip xz
- Make

And of course depencies are allowed to be inputed to mkDerivation

- nativeBuildInputs -> compile time deps
- buildInputs -> run time deps
- progagatedBuildInputs -> run time deps of scripts, useful for Python-like scripting language
- checkInputs -> test deps, you can drop them if you are aiming at cross compilation

Later this can be cross-compiled.

### stages

- dontUnpack
- dontPatch
- dontConfigure
- dontBuild
- doCheck
- dontIntall
- dontFixup
- doInstallCheck
- doDist

You can see that by default, Check stage, Install Check stage and Dist stage is disabled.

### Hands on

```nix
let
  pkgs = import <nixpkgs> { };
in
pkgs.stdenv.mkDerivation {
  name = "hello";
  src = ./hello-2.9.tar.gz;

  nativeBuildInptus = [
    pkgs.help2man
  ];

  patches = [
    ./my.patch
  ];

  configPhase = ''
    ./configure --prefix $out
  '';

  buildPhase = ''
    make
  '';

  doCheck = false;
  checkPhase = ''
    make check
  '';

  installPhase = ''
    make install
  '';
}
```

This shows a way I change the hello.c to print hello nixos, and I then can build from scratch this project.

What is exactly happening? So nix is actually doing a lot of bash shell scripting at the back and trying to detect whether some file exists in the project. If exists, it will try to run some command like `make` and `make install`.

### Debugging the Nix builds

`nix-build --keep-failed`: Will keep the env file and the source folder that might be damaged.

`nix-build --debug`: This will print a lot more information about what is being built.

`pkgs.breakpointHook` would freeze your drv, and let you attach to your sandbox.

`set -x` can be added to PreConfigure phase, this might be a more straightforward way.z

### Pinning nixpkgs

If you open the nix repl and toString the nixpkgs, you will find a folder on the os.

To make nix expressions build forever, it is possible to pin all the inputs.

nix supports output-address, like `fetchurl`, `fetchTarball`, inputs my varied, output is fixed, network allowed in the network.

There are some tools that allow you to do that too. `niv`, `npins`, `nixtamal`. Compared to `flake`, they may have other advantages.

Let's try nitamal.

```bash
nix-shell -p nix-tamal

nixtamal set-up #this step will fetch another tarball of source so it might take some
```

Now you can modify the default.nix using this

```nix
let
  sources = import ./nix/tamal { };
  pkgs = import sources.nixpkgs { };
```

### Fetching url

In the following instead of we providing the source code, we provide a link to fetch the tarball.

But something to be noticed here, first url can be a list, which means that you can add mirror.

Secondly, the nix only checks the hash to make sure it is the same directory, so if you dont change the has and just change the url, nix will choose not to connect to the Internet.

```nix
  name = "hello-2";
  src = pkgs.fetchurl {
    url = "https://gnu.mirror.constant.com/hello/hello-2.9.tar.gz";
    hash = "sha256-7Lt6IhQZbFf/k0CqcUWOFVmr049tjRaWZoRpNd8ZHqc=";
  };
```

There are many more fetches

`fetchzip` will auto unpack
`fetchpatch` will normalize patch
`fetchgipt` supports submodules

`nix-prefetch-git/url` will put something in the NixStore, and you can check the information, this is gery good for large downloads.

### Language-specific builders

Languge-specific builders are one level higher abstraction compared to stdenv.mkDerivation.

Just read the nixpkgs manual, I think you can find the necessary options, like `buildPythonPackage`, `buildPythonApplication`

### Build Helpers

Build Helpers are wrapper function around mkDerivation that are helpful for recurring tasks like the following

- Create a preconfigured nix shell
- Running simple scripts to generate package outputs
- Creating prepackages standalond script
- Creating text files
- Batch-Symlinking of scattered paths

`pkgs.mkShell`: Create a development shell

```nix
let
	pkgs = import <nixpkgs> {};
	myPython = pkgs.python313.withPackages (ps: with ps; [flask numpy requests]);
in
	pkgs.mkShell {
		packages = [
			myPython;
			pkgs.python312.pkgs.black
			pkgs.python314.pkgs.mypy
		];
	}
```

`pkgs.runCommand`: fetch some environment, and run some command to the output. Very flexible and useful commands.

```nix
let
	pkgs = import <nixpkgs> {};
	env = {
		nativeBuildInputs = [ pkgs.cowsay ];
	};
in
pkgs.runCommand "cowsay-output" env ''
find "${pkgs.cowsay}/share/cowsay/cows" \
-name "*.cow" \
-exec cowsay -f {} "Hello Nix Users" >> $out \;
''
```

`pkgs.writeShellApplication`: What it does is to grab the environment, then build a kind of shell application using the text

```nix
pkgs.writeShellApplication {
	name = "show-nixos-org";

	runtimeInputs = with pkgs; [ curl w3m ];

	text = ''
		curl -s 'https://nixos.org | w3m -dump -T text/html
	'';
}
```

`pkgs.synlinkJoin`: Just take all the bin folders and expose them as one folder

```nix
pkgs.symlinkJoin {
	name = "myFavouriteApps";
	paths = with pkgs; [ hello cowsay fortune ];
}
```

## Composing nixpkgs

We need to modularize the project structure, because if we build a lot of small sandboxes instead of a large everything sandbox, then we enjoy better build speed when we modify something.

### Call Package Pattern

Here is an example of ./a/default.nix

```nix
{ stdenv, boost, openssl, withFeatureX ? false}:

stdenv.mkDerivation {
	name = "my-app";
	src = ./.;
	buildInputs = [
		boost
		openssl
	];
#...
}
```

Usage: pkgs.callPackage ./a/default.nix

An example would be the following default.nix:

```nix
{ stdenv, fetchzip, help2man }:

stdenv.mkDerivation {
  name = "hello";

  src = fetchzip {
    url = "https://gnu.mirror.constant.com/hello/hello-2.9.tar.gz";
    sha256 = "sha256-1aFStdB6F9qR8hch6QTZZQm5rgEhh1SbNIfFs61FsK8=";
  };

  patches = [
    ./hello-nix.patch
  ];

  nativeBuildInputs = [
    help2man
  ];
}
```

Question: Where did I get the stdenv, fetchzip and help2man from?

You use the call Package pattern, by using a release.nix to call

```nix
let
	source  = improt ./nix/tamal {};
	pkgs = import sources.nixpkgs {};
	hello-gcc = pkgs.callPackage ./default.nix {};
in
{
	inherit hello-gcc;
	hello-clang = hello-gcc.override{
	stdenv = pkgs.clangStdenv;
	};

	hello-arm = pkgs.pkgsCross.aarch64-multiplatform.callPackage ./default.nix {}
}
```

Now you can use `nix build release.nix -A hello-gcc / hello=clang`.

You can even cross-compile the program into arm system. Aren't you surprised? you should be

### How callPackage works

You can test it in nix repl.

```nix
cp = pkgs.lib.callPackage {a = 1; b = 10; c = 100;}

# cp kind of knows like hey I have these values, if you give me a function I can plug in.

f = {a , b} : a + b

cp f {} # would evaluate to 11

cp {{a, d}: a + d} {d = 1000;} # would evaluate to 1001

```

This is not really that interesting

```nix
f = {  x , y, z}: {result = x + y + z;}

myCallPackage = pkgs.lib.callPackageWith { x = 1; y = 10;}

foo = myCallPackage f {z = 100;}

foo.result

(foo.override {x = 2;}).result;

```

This is a core pattern. foo here rememebrs everything we have called and remembered the values.

### The user of override

Here is an example of what usePackager with override gives you

```nix
let pkgs = improt <nixpkgs> {};
	a = pkgs.callPackage ./a/default.nix {};
in
{
	inherit a;

	a-static = a.override {
		staticBuild = true;
		openssl = pkgs.openssl.override {static = true};
	};

	a-patchedversion = a.overrideAttrs (oldAttrs: {
		patches = oldAttrs.patches or [] ++ [
			./patches/specialstuff.patch
		];
	});
}
```

The override just taks an attrset as an argument, while the overrideAttrs taks a high level function that wors on a specific values?

So this is confusing, right? When to use what?

override changes the input of the callPackags, like stdenv, packageA, packageB. overrideAttrs change the things inside stdenv.mkDerivation!

And inside release.nix

```nix
{
	package1 = ...;
	package2 = ...;
	package3 = ...;
}

```

`nix-build release.nix` will build all the derivations. `nix-build release.nix -A package2` will only build package 2 as a derivaiton.

When you are using attrset overrides, a good pattern is always to use `old.xxx or [] ++ [pkgs.help2man]`. You do not want destructive rebuild, correct?

`pkgs.lib.optional true xxx` would return the list with xxx in it, while `pkgs.lib.optional false xxx` would return an empty list.

`pkgs.lib.optionals` is another method that returns the list because it also takes the list.


### Anti-Patterns

```nix
with import <nixpkgs> {};
with lib;

stdenv.MkDerivaiton[I {
	buildInputs = foo [a b c ];
}
```

Bad, name could clash, I dont know function used later is belong to what.


```nix
let 
	pkgs = import <nixpkgs> {};
	inherit (pkgs) stdenv a b c;
	inherit (pkgs.lib) foo;
in
stdenv.MkDerivaiton[I {
	buildInputs = foo [a b c ];
}
```


Good, name is clear where it is from.


```nix
rec {
	x = 1;
	y = 2;
	z = x + y;
}
```

Bad, pointless.

```nix
let 
	x = 1;
	y = 2;
in
{
	inherit x, y;
	z = x + y;
}
```

Good, very clean. Imagin doing this in a 500 lines of attrset, you will understand rec can bring chaos.


```nix
stdenv.mkDerivation rec{
	name = "bla";
	version = "1.2.3";
	
	src = someFetcher {
		url = "...${name}...${version}...";
		hash = "...";
	}
}
```

Surprisingly if you try to overrwrite the version, it does not change url


```nix
stdenv.mkDerivation (finalAttrs: {
  pname = "bla";
  version = "1.2.3";

  src = someFetcher {
    url = "...${finalAttrs.pname}...${finalAttrs.version}...";
    hash = "...";
  };
})
```

Good, override will work. 

Only have one nixpkgs import.

Dont directly overwrite the whole phase, remember to add prehook and posthook. 

Avoid nested packages call as it will create a lot of overrides.


### Import from Derivaiton

This is probably an anti-pattern. Mighty but with tradeoffs.

What it does is first use a nix to generate a nix file, then use another file to callPackages on the generated nix file.

```nix
# default.nix

let
  pkgs = import <nixpkgs> {};
  hello = pkgs.callPackage ./generate-nix-expr.nix {};
in
pkgs.callPackage "${hello}/hello.nix" {}
```

```nix
# generate-nix-expr.nix

{ runCommand }:

runCommand "gen-nix-expr" {} ''
  mkdir $out

  echo "generating nix expression"
  sleep 6 # simulate slow generation

  cat << EOF > $out/hello.nix

{ stdenv, hello }:
stdenv.mkDerivation {
  name = "hello2";
  src = hello.src;
}

EOF
```


The bad part is, a relevant change to the generator produces a new derivation/store location, even when executing that derivation ultimately generates the same file contents.

## Advanced Packaging topics
### Source filtering with lib.fileset

Here is a bad example.
```nix
stdenv.mkDerivation {
	pname = "bla";
	
	src = ./.;
	
	#...
}
```

Everything inside the src folder will be copied to Nix Store.

With source filters, we have more cache hits, and fewer rebuilds, and finally fewer and smaller sources copies into the nix store.

1. Solution 1
```nix
src = pkgs.lib.cleanSource ./.;
```
This will clean symlink, .o etc...


2. Solution 2
```nix
src = lib.cleanSourceWith {
	filter = path: _type: !lib.hasSuffix ".nix" path;
	src = lib.cleanSource ./.;
};
```
This filters out all the nix file, and when we are inside sandbox nix files are indeed not needed.

3. Standard
```nix
src = lib.fileset.toSource {
	root = ./.;
	fileset = lib.fileset.unions [
	./include
	./test
	./example
	./CMakeLists.txt
	./pkg-config.pc.cmake
	];
};
```
This defines all the files union that you actually want.


4. Only Copy source files with certain file type
```nix
let
	fs = lib.fileset;
	extensionOf = extensions: file: 
		builtins.any file.hasExt extensions;
in
fs.toSource {
	root = ./.;
	fileset = fs.unions [
		./.latexmkrc
		(fs.Filefilter (extensionsOf [ "jpg" "pdf" "png" "tex"]) ./.)
	];
}
```


5. Subtract one file list from the other
```nix
let
	fs = lib.fileset;
	nixFiles = fs.fileFilter (file: file.hasExt "nix") ./.;
in
fs.toSource {
	root = ./.;
	fileset = fs.difference (fs.gitTracked ./.) nixFiles;
}
```

If you dont understand why some source files are not included, or included, you can use the following command
```nix
lib.fileset.traceVal
```

But if you start debugging it, it might be a sign that you are doing something too complex already...

