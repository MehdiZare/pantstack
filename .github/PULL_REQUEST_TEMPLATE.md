## Summary

Describe the change and the motivation.

## Version Impact (Required for dev→main PRs)

**⚠️ For PRs from `dev` to `main`, you MUST add ONE of these labels:**
- `release:major` - Breaking changes (1.0.0 → 2.0.0)
- `release:minor` - New features (1.0.0 → 1.1.0)
- `release:patch` - Bug fixes (1.0.0 → 1.0.1)
- `release:skip` - No version bump needed (docs, CI tweaks)

## Checklist

- [ ] PR title follows [Conventional Commits](https://www.conventionalcommits.org/) format OR has a release label
- [ ] For dev→main PRs: Added appropriate version label (see above)
- [ ] Tests pass locally (`make test`) and in CI
- [ ] Pre-commit passes locally (`pre-commit run --all-files`)
- [ ] If infra changes, PR preview or preview plan reviewed
- [ ] Docs/README updated if needed

