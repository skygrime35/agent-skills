#!/usr/bin/env bash
set -e
git init -q -b main .
git config user.name "Fixture"
git config user.email "fixture@example.com"
mkdir -p .github/workflows app/migrations
cat > .github/workflows/deploy.yml <<'YML'
name: deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh production
YML
printf '#!/bin/sh\necho deploying to "$1"\n' > deploy.sh
printf '# Shop\n' > README.md
touch app/__init__.py app/migrations/__init__.py
cat > app/migrations/0001_initial.py <<'PY'
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[("id", models.AutoField(primary_key=True)), ("legacy_col", models.CharField(max_length=50))],
        ),
    ]
PY
git add .github deploy.sh README.md app
git commit -q -m "Initial release"
git checkout -q -b develop
cat > app/migrations/0002_drop_col.py <<'PY'
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("app", "0001_initial")]
    operations = [
        migrations.RemoveField(model_name="order", name="legacy_col"),
    ]
PY
git add app/migrations/0002_drop_col.py
git commit -q -m "Drop legacy_col from Order"
printf '\nNow with order history.\n' >> README.md
git add README.md
git commit -q -m "Update README"
