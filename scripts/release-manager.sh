#!/bin/bash

# Unified Release Manager Script
# This script can be used to:
# 1. Bump the version
# 2. Create a release
# 3. Do both

set -e

# Ensure we're in the project root
cd "$(git rev-parse --show-toplevel)" || exit 1

# Default values
ACTION="both"
BUMP_TYPE="patch"
CREATE_TAG=true
PUSH_TAG=true
CREATE_RELEASE=true

# Help function
show_help() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -h, --help                 Show this help message"
  echo "  -a, --action ACTION        Action to perform: bump, release, or both (default: both)"
  echo "  -t, --type TYPE            Version bump type: patch, minor, or major (default: patch)"
  echo "  --no-tag                   Don't create a git tag"
  echo "  --no-push                  Don't push changes to remote"
  echo "  --no-release               Don't create a GitHub release"
  echo ""
  echo "Examples:"
  echo "  $0                         # Bump patch version, create tag, push, and create release"
  echo "  $0 -a bump -t minor        # Only bump minor version, create tag and push"
  echo "  $0 -a release              # Only create release for current version"
  echo "  $0 --no-release            # Bump version, create tag, push, but don't create release"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -h|--help)
      show_help
      exit 0
      ;;
    -a|--action)
      ACTION="$2"
      shift
      shift
      ;;
    -t|--type)
      BUMP_TYPE="$2"
      shift
      shift
      ;;
    --no-tag)
      CREATE_TAG=false
      shift
      ;;
    --no-push)
      PUSH_TAG=false
      shift
      ;;
    --no-release)
      CREATE_RELEASE=false
      shift
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# Validate action
if [[ ! "$ACTION" =~ ^(bump|release|both)$ ]]; then
  echo "Error: Invalid action '$ACTION'. Must be 'bump', 'release', or 'both'."
  show_help
  exit 1
fi

# Validate bump type
if [[ ! "$BUMP_TYPE" =~ ^(patch|minor|major)$ ]]; then
  echo "Error: Invalid bump type '$BUMP_TYPE'. Must be 'patch', 'minor', or 'major'."
  show_help
  exit 1
fi

# Get current branch and extract Odoo version
get_odoo_version() {
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  ODOO_VERSION=$(echo "$BRANCH" | grep -oE '[0-9]+\.[0-9]+' || echo "unknown")
  echo "$ODOO_VERSION"
}

# Get current version from manifest
get_current_version() {
  MANIFEST_FILE=$(find . -name "__manifest__.py" | head -1)
  if [ -z "$MANIFEST_FILE" ]; then
    echo "No __manifest__.py file found"
    exit 1
  fi

  # Extract version
  VERSION=$(grep -E "'version':\s*'[0-9]+\.[0-9]+\.[0-9]+'" "$MANIFEST_FILE" | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" || echo "")
  if [ -z "$VERSION" ]; then
    echo "Failed to extract version from $MANIFEST_FILE"
    exit 1
  fi
  
  echo "$VERSION"
}

# Bump version
bump_version() {
  local current_version=$1
  local bump_type=$2
  local odoo_version=$3
  
  echo "Current version: $current_version"
  echo "Bump type: $bump_type"
  echo "Odoo version: $odoo_version"
  
  # Parse version
  IFS='.' read -r -a VERSION_PARTS <<< "$current_version"
  MAJOR=${VERSION_PARTS[0]}
  MINOR=${VERSION_PARTS[1]}
  PATCH=${VERSION_PARTS[2]}
  
  # Calculate new version
  if [ "$bump_type" == "major" ]; then
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
  elif [ "$bump_type" == "minor" ]; then
    MINOR=$((MINOR + 1))
    PATCH=0
  else
    PATCH=$((PATCH + 1))
  fi
  
  NEW_VERSION="$MAJOR.$MINOR.$PATCH"
  echo "New version: $NEW_VERSION"
  
  # Update manifest
  MANIFEST_FILE=$(find . -name "__manifest__.py" | head -1)
  
  # Update manifest version with better pattern matching
  if ! sed -i "s/'version':\s*'$current_version'/'version': '$NEW_VERSION'/g" $MANIFEST_FILE; then
    echo "Failed to update version in manifest file"
    exit 1
  fi
  
  # Verify the change was made
  if ! grep -q "'version': '$NEW_VERSION'" $MANIFEST_FILE; then
    echo "Version update verification failed. Trying alternative pattern."
    # Try an alternative pattern
    sed -i "s/\"version\":\s*\"$current_version\"/\"version\": \"$NEW_VERSION\"/g" $MANIFEST_FILE
  fi
  
  # Check if there are changes to commit
  if ! git diff --quiet $MANIFEST_FILE; then
    # Commit the version change
    git add $MANIFEST_FILE
    git commit -m "chore: bump version to $NEW_VERSION"
    
    echo "Version bumped to $NEW_VERSION"
    
    # Create tag if requested
    if [ "$CREATE_TAG" = true ]; then
      TAG="v$NEW_VERSION-odoo$odoo_version"
      echo "Creating tag $TAG"
      git tag "$TAG"
      
      # Push changes if requested
      if [ "$PUSH_TAG" = true ]; then
        echo "Pushing changes and tag to remote"
        git push origin HEAD
        git push origin "$TAG"
      fi
    fi
  else
    echo "No changes detected in manifest file. Version might already be updated."
    exit 1
  fi
  
  echo "$NEW_VERSION"
}

# Generate changelog
generate_changelog() {
  local version=$1
  local odoo_version=$2
  local tag="v$version-odoo$odoo_version"
  
  echo "Generating changelog for version $version (tag $tag) for Odoo $odoo_version"
  
  # Find previous tag
  PREVIOUS_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")
  echo "Previous tag: $PREVIOUS_TAG"
  
  echo "# Release $version for Odoo $odoo_version" > changelog.md
  echo "" >> changelog.md
  
  # Check for manual release notes
  if [ -f "RELEASE_NOTES.md" ]; then
    echo "Found RELEASE_NOTES.md, including in changelog"
    echo "## Release Notes" >> changelog.md
    cat RELEASE_NOTES.md >> changelog.md
    echo "" >> changelog.md
  fi
  
  if [ -z "$PREVIOUS_TAG" ]; then
    # First release - get all commits
    echo "No previous tag found, including all commits"
    echo "## Changes" >> changelog.md
    git log --pretty=format:"* %s" | grep -v "chore: bump version" | grep -v "Merge pull request" | head -50 >> changelog.md || echo "* Initial release" >> changelog.md
  else
    # Group changes by type
    echo "## Changes since $PREVIOUS_TAG" >> changelog.md
    echo "" >> changelog.md
    
    # Get all commits first without the bullet point
    ALL_COMMITS=$(git log ${PREVIOUS_TAG}..HEAD --pretty=format:"%s")
    
    # Features
    FEATURES=$(echo "$ALL_COMMITS" | grep "^feat" | sed 's/^/* /' || echo "")
    if [ -n "$FEATURES" ]; then
      echo "### ✨ New Features" >> changelog.md
      echo "$FEATURES" >> changelog.md
      echo "" >> changelog.md
    fi
    
    # Fixes
    FIXES=$(echo "$ALL_COMMITS" | grep "^fix" | sed 's/^/* /' || echo "")
    if [ -n "$FIXES" ]; then
      echo "### 🐛 Bug Fixes" >> changelog.md
      echo "$FIXES" >> changelog.md
      echo "" >> changelog.md
    fi
    
    # Other changes - excluding PR merges and version bumps
    OTHER=$(echo "$ALL_COMMITS" | 
           grep -v "^feat" | 
           grep -v "^fix" | 
           grep -v "chore: bump version" | 
           grep -v "Merge pull request" | 
           sed 's/^/* /' || echo "")
    if [ -n "$OTHER" ]; then
      echo "### 🔄 Other Changes" >> changelog.md
      echo "$OTHER" >> changelog.md
    fi
    
    # If no changes were found, add a default message
    if [ -z "$FEATURES" ] && [ -z "$FIXES" ] && [ -z "$OTHER" ]; then
      echo "### Changes" >> changelog.md
      echo "* Maintenance release" >> changelog.md
    fi
  fi
  
  echo "Changelog generated:"
  cat changelog.md
}

# Create release
create_release() {
  local version=$1
  local odoo_version=$2
  local tag="v$version-odoo$odoo_version"
  
  # Check if tag exists
  if ! git rev-parse "$tag" >/dev/null 2>&1; then
    if [ "$CREATE_TAG" = true ]; then
      echo "Tag $tag does not exist. Creating it now."
      git tag "$tag"
      
      if [ "$PUSH_TAG" = true ]; then
        echo "Pushing tag to remote"
        git push origin "$tag"
      fi
    else
      echo "Error: Tag $tag does not exist and --no-tag option is set."
      exit 1
    fi
  fi
  
  # Generate changelog
  generate_changelog "$version" "$odoo_version"
  
  # Create zip file
  echo "Creating zip file..."
  ZIP_FILE="monei-odoo-$version-odoo$odoo_version.zip"
  zip -r "$ZIP_FILE" . \
    -x '*.git*' \
    -x '*/.github/*' \
    -x '*.pyc' \
    -x '__pycache__/*' \
    -x '*/.DS_Store' \
    -x '*/._*' \
    -x 'changelog.md' \
    -x "$ZIP_FILE"
  
  echo "Zip file created: $ZIP_FILE"
  
  # Create GitHub release if requested
  if [ "$CREATE_RELEASE" = true ]; then
    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
      echo "GitHub CLI (gh) is not installed. Please install it to create a release."
      echo "You can manually create a release on GitHub using the generated changelog and zip file."
      return
    fi
    
    echo "Creating GitHub release..."
    gh release create "$tag" \
      --title "Release $version (Odoo $odoo_version)" \
      --notes-file changelog.md \
      "$ZIP_FILE"
    
    echo "Release created successfully!"
  else
    echo "Skipping GitHub release creation."
    echo "You can manually create a release on GitHub using the generated changelog and zip file."
  fi
}

# Main execution
ODOO_VERSION=$(get_odoo_version)
CURRENT_VERSION=$(get_current_version)
NEW_VERSION=$CURRENT_VERSION

echo "Working with Odoo version: $ODOO_VERSION"

# Perform the requested action
if [[ "$ACTION" == "bump" || "$ACTION" == "both" ]]; then
  NEW_VERSION=$(bump_version "$CURRENT_VERSION" "$BUMP_TYPE" "$ODOO_VERSION")
fi

if [[ "$ACTION" == "release" || "$ACTION" == "both" ]]; then
  create_release "$NEW_VERSION" "$ODOO_VERSION"
fi

echo "Done!" 