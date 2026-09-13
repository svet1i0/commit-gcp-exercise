# Human access (project IAM) — additive google_project_iam_member only.
# Do not use google_project_iam_policy / google_project_iam_binding here:
# authoritative or role-wide bindings can strip unrelated members.

locals {
  # Exercise reviewer_member folds into the same generic map (input-only switch user:/group:).
  exercise_reviewer_binding = var.reviewer_member == "" ? {} : {
    exercise_reviewer = {
      role    = "roles/viewer"
      members = toset([var.reviewer_member])
    }
  }

  human_access_merged = merge(var.human_access_bindings, local.exercise_reviewer_binding)

  # Stable for_each keys: "<binding_key>|<member>"
  human_access_member_pairs = merge([
    for binding_key, binding in local.human_access_merged : {
      for member in binding.members :
      "${binding_key}|${member}" => {
        role   = binding.role
        member = member
      }
    }
  ]...)
}

resource "google_project_iam_member" "human_access" {
  for_each = local.human_access_member_pairs

  project = var.project_id
  role    = each.value.role
  member  = each.value.member
}
