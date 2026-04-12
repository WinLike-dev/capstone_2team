# Next Steps For `test/all`

This file summarizes the remaining manual work for the current GCP setup.

Current fixed values:

- backend public IP: `34.50.45.68`
- backend private IP: `10.178.0.2`
- AI public IP: `34.50.21.162`
- AI private IP: `10.178.0.3`
- frontend URL: `https://capstone-2team-test-all.vercel.app`
- backend HTTPS hostname: `https://34.50.45.68.nip.io`
- deploy branch: `test/all`

## 1. Set Vercel env

Add this environment variable in Vercel:

```env
NEXT_PUBLIC_BACKEND_URL=https://34.50.45.68.nip.io
```

Then redeploy the frontend.

## 2. Create one SSH deploy key pair

Run this on your local machine:

```powershell
ssh-keygen -t ed25519 -C "github-actions-deploy" -f $HOME\.ssh\healthmate_github_actions
```

Files created:

- private key: `$HOME\.ssh\healthmate_github_actions`
- public key: `$HOME\.ssh\healthmate_github_actions.pub`

## 3. Add the public key to both VMs

On each VM:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Append the contents of `healthmate_github_actions.pub` to `authorized_keys`.

## 4. Add GitHub Actions secrets

Repository secrets:

- `GCP_SSH_PRIVATE_KEY`
- `GCP_BACKEND_HOST`
- `GCP_AI_HOST`
- `GCP_BACKEND_ENV`
- `GCP_AI_ENV`

Recommended values:

```text
GCP_BACKEND_HOST=34.50.45.68
GCP_AI_HOST=34.50.21.162
```

For `GCP_BACKEND_ENV`, paste the full contents of:

- `develop/deploy/gcp-two-vm/backend/.env.backend`

For `GCP_AI_ENV`, paste the full contents of:

- `develop/deploy/gcp-two-vm/ai/.env.ai`

For `GCP_SSH_PRIVATE_KEY`, paste the full contents of:

- `$HOME\.ssh\healthmate_github_actions`

## 5. Fix firewall rules

Backend VM:

- keep `80` open to the internet
- keep `443` open to the internet
- keep `22` open for SSH-based deploy access
- remove public `8080`

AI VM:

- keep `22` open for SSH-based deploy access
- allow `8000` only from `10.178.0.2/32`
- do not allow public `8000`

## 6. Push `test/all`

```powershell
git add .gitignore .github/workflows/gcp-two-vm-deploy.yml develop/deploy/gcp-two-vm
git commit -m "chore: add GCP two-vm deploy pipeline"
git push origin test/all
```

## 7. Watch the first deploy

In GitHub:

- `Actions`
- `Deploy GCP Two VM`

Expected result:

- Docker gets installed automatically on both Ubuntu VMs if missing
- backend deploys to `34.50.45.68`
- AI deploys to `34.50.21.162`

## 8. Verify after deploy

From your browser:

- `https://34.50.45.68.nip.io/api/health`

From backend VM:

```bash
curl http://10.178.0.3:8000/health
```

From the frontend:

- open `https://capstone-2team-test-all.vercel.app`
- test login, chat, and home recommendations
