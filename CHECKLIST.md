# CipherLab Project — Checklist

## Phase A — Initial Inspection
- [ ] Confirm the current project directory: C:\project\Kriptografi
- [ ] Inspect the complete project structure and existing source code
- [ ] Inspect Git status, current branch, commit history, and remotes
- [ ] Inspect the target GitHub repository: https://github.com/zann06/Enskripsi-Block-Cipher
- [ ] Identify existing features, missing functionality, and potential risks
- [ ] Preserve existing work and history before making changes

## Phase B — Application Finalization
- [ ] Verify the existing application architecture and preserve it where practical
- [ ] Verify the cipher implementation and documented key schedule
- [ ] Verify encryption and decryption
- [ ] Verify ECB mode
- [ ] Verify CBC mode
- [ ] Verify CTR mode
- [ ] Verify padding, input validation, and error handling
- [ ] Verify the handling of empty inputs and multi-block data
- [ ] Verify PDF report generation and downloading
- [ ] Improve UI/UX and remove unfinished or nonfunctional components
- [ ] Resolve discovered bugs without unnecessarily rewriting working code

## Phase C — Testing
- [ ] Verify the dependencies and installation instructions
- [ ] Run available automated tests
- [ ] Add missing tests for important functionality
- [ ] Fix failing tests where possible
- [ ] Rerun tests after fixes
- [ ] Verify the application starts using its actual documented command
- [ ] Verify PDF generation with actual application data
- [ ] Record actual test results and disclose anything not verified

## Phase D — Public Repository Cleanup
- [ ] Create or update a professional root README.md in English
- [ ] Verify README setup, usage, and testing commands
- [ ] Update .gitignore for the actual technology stack
- [ ] Remove unnecessary internal planning files such as PRD.md and PROMPT.md when they are not needed publicly
- [ ] Retain the root README.md
- [ ] Review every remaining Markdown file and keep only useful public documentation
- [ ] Exclude virtual environments, caches, temporary files, and unnecessary generated artifacts
- [ ] Check for API keys, passwords, tokens, .env files, and other sensitive information
- [ ] Verify that essential source files, tests, and configuration files are retained
- [ ] Add a LICENSE only if the licensing choice is intentional and compatible with the existing project

## Phase E — GitHub Preparation
- [ ] Confirm the remote points to zann06/Enskripsi-Block-Cipher
- [ ] Confirm the correct target branch
- [ ] Inspect local and remote changes before synchronizing
- [ ] Preserve existing remote commits and repository history
- [ ] Stage only the intended project files
- [ ] Inspect the staged file list and diff
- [ ] Verify that README.md is included
- [ ] Verify that unnecessary internal documents and secrets are excluded
- [ ] Run git diff --cached --check
- [ ] Create a descriptive commit

## Phase F — Publish and Verify
- [ ] Push the commit to the existing GitHub repository
- [ ] Confirm the push succeeded
- [ ] Verify the remote branch contains the new commit
- [ ] Verify the final repository contents and README
- [ ] Provide the final repository URL, branch, commit hash, test results, and remaining limitations