---
id: kb-005
title: Permission denied and IAM errors
category: access
---

When you see "permission denied" or `PERMISSION_DENIED`, the issue is almost always one of:

1. **Missing IAM role** — the principal making the call doesn't have the required role on the resource
2. **Wrong principal** — the request is being made by a different account than you expect (common with service accounts)
3. **Conditional binding** — the role exists but a condition (time, IP, resource attribute) is blocking it

To diagnose:

- Open Logs Explorer and look for the failing request
- Check the `protoPayload.authenticationInfo.principalEmail` field to confirm the calling identity
- Check `protoPayload.authorizationInfo` to see which permission was denied

Once you've identified the missing permission, grant the corresponding role to the principal in IAM & Admin → IAM. Use predefined roles (Viewer, Editor, Admin) where possible; use custom roles only when you need finer-grained permissions.
