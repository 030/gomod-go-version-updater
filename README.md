# gomod-go-version-updater-action

The rationale for this action is that
[Dependabot cannot](https://github.com/dependabot/dependabot-core/issues/9057)
update the go version that is defined in a `go.mod` file.

## Development

```zsh
pip install pyinstaller==v6.10.0
pyinstaller --onefile main.py --name gomod-go-version-updater
./dist/gomod-go-version-updater
```

## Usage

1. To use this action, ensure that:
   `Allow GitHub Actions to create and approve pull requests` option has been
   enabled in the action settings. In order to find this, attach:
   `/settings/actions` to the project URL, i.e.:
   `https://github.com/<owner>/<project-name>/settings/actions`.
1. Once the setting has been enabled, create a
   `~/.github/workflows/gomod-go-version-updater.yml` file with the following
   content:
   ```yaml
   ---
   name: gomod-go-version-updater-action
   "on":
     schedule:
       - cron: "42 6 * * *"
   permissions:
     contents: write
     pull-requests: write
   jobs:
     gomod-go-version-updater-action:
       runs-on: ubuntu-22.04
       steps:
         - uses: 030/gomod-go-version-updater-action@v0.1.6
   ```
1. To ensure that an action is triggered for testing the Golang version update,
   add a `pull_request_review` trigger. This will cause a specific Workflow
   Action to run whenever someone submits a review for the pull request created
   by the **gomod-go-version-updater-action**:
   ```yaml
   "on":
     # required by gomod-go-version-updater to trigger this action once pr has
     # been reviewed
     pull_request_review:
       types: [submitted]
   ```
1. Optional: if private go modules have to be downloaded:
   ```yaml
   - uses: 030/gomod-go-version-updater-action@v0.1.6
     with:
       github-token-for-downloading-private-go-modules: ${{ secrets.GITHUB_TOKEN }}
   ```
1. Optional: set the log level to `DEBUG`, `WARNING`, `ERROR` or `CRITICAL`
   (default: INFO):
   ```yaml
   - uses: 030/gomod-go-version-updater-action@v0.1.6
     with:
       gomod-go-version-updater-action-log-level: DEBUG
   ```

## Test

See the run steps that are defined in
[this GitHub Workflow](.github/workflows/python.yml).
