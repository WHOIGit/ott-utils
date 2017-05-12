# Utilities for working with IFCB summary data

## Installation via Anaconda

It is recommended to use Anaconda to install ott-utils.

```
conda env create -f environment.yml
source activate ott-utils
```

## Installation via Anaconda for development purposes

ott-utils depends on pyifcb which is currently under development.
To enable yourself to update pyifcb and still use it, build the
ott-utils-dev environment following these steps:

```
conda env create -f environment-dev.yml
source activate ott-utils-dev
git clone https://github.com/joefutrelle/pyifcb
cd pyifcb
python setup.py develop
```

Then, when you want to update pyifcb and use it in ott-utils,
change directories to pyifcb and run

```
git pull
```