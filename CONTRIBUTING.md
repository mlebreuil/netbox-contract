# Contributing

Contributions are welcome!

## Types of contributions

### Report bugs or submit feedback

Report bugs and submit feetback [here](https://github.com/mlebreuil/netbox-contract/issues).

### Fix bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

### Implement features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

## Coding conventions
 
Netbox [Style Guide](https://netboxlabs.com/docs/netbox/en/stable/development/style-guide/)  
Django [Coding style](https://docs.djangoproject.com/en/stable/internals/contributing/writing-code/coding-style/)  

## linting

The [ruff](https://docs.astral.sh/ruff/) linter is used to enforce code style. A [pre-commit hook](./getting-started.md#3-enable-pre-commit-hooks) which runs this automatically is included with NetBox. To invoke `ruff` manually, run:

```
python3 -m pip install ruff
ruff check netbox_contract/
```


The pre-commit Python framework is used to simplify the managment of pre-commit hooks.  
Config is stored in .pre-commit-config.yaml   

## Repository structure

There are 2 permanent branch in the repository:

* master - The current stable release. Individual changes should never be pushed directly to this branch, but rather merged from develop.
* develop - Active development for the upcoming patch release. Pull requests will typically be based on this branch unless they introduce breaking changes that must be deferred until the next minor release.

For each new feature or bug fix a branch is created from the corresponding issue.

## Setup your development environment


1. [Install Netbox](https://github.com/netbox-community/netbox/blob/develop/docs/installation/).
Make sure taht at the Netbox installtion step you follow the "Option B: Clone the Git Repository"

2. From the Netbox directory you activate the NetBox virtual environment 

    ```
    $ cd netbox
    $ source venv/netbox/bin/activate
    ```
 
3. Fork the [netbox-contract](https://github.com/mlebreuil/netbox-contract/) repo on GitHub.
4. Clone your fork locally

    ```
    $ cd ..
    $ git clone git@github.com:your_name_here/netbox-contract.git
    ```

5. Add the plugin to NetBox virtual environment:

    ```
    $ cd  netbox-contract
    $ python3 -m pip install -e .
    ```

6. install pre-commit:

    ```bash
    python -m pip install pre-commit
    pre-commit install
    ```

6. Update the Netbox configuration and run the database migrations as mentionned in the plugin installation steps.

7. Create a branch for local development:

    ```
    $ git checkout -b name-of-your-bugfix-or-feature
    ```

    Make your changes locally.

8. You can test your changes using the django development server:

    ```
    $ python3 netbox/netbox/manage.py runserver 0.0.0.0:8000 --insecure
    ```

    Connect to the name or IP of the server (as defined in ALLOWED_HOSTS) on port 8000; for example, http://127.0.0.1:8000/.

9. Run unittest

    ```
    $ python3 netbox/netbox/manage.py test netbox_contract
    ```

10. Commit your changes and push your branch to GitHub:

    ```
    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature
    ```

1. Submit a pull request through the GitHub website.

## Model changes

Create the migrations:  

```bash
source netbox/venv/bin/activate
python3 netbox/netbox/manage.py makemigrations netbox_contract --dry-run
python3 netbox/netbox/manage.py makemigrations netbox_contract
```

Apply the migrations:  

```bash
source netbox/venv/bin/activate
python3 netbox/netbox/manage.py migrate
```

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. 
3. The pull request should work for Python 3.10 and 3.11. Check [Actions](https://github.com/mlebreuil/netbox-contract/actions)
   and make sure that the tests pass for all supported Python versions.


## Deploying

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in CHANGELOG.md) and that all tests pass.
Then in the github project go to `Releases` and create a new release with a new tag.  This will automatically upload the release to pypi:
