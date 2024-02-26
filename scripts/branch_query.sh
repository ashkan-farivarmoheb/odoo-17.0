gitsha="$1"
token="$2"

echo "Calling branch query"

# Print the arguments
echo "gitsha: $gitsha"

# Fetch all branches
git fetch --all;

curl -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${token}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/ashkan-farivarmoheb/odoo-17.0/git/ref/cd95a49e4d7dc37478b7bdff7e6d718ebb084a75

# Check if the commit exists
if git rev-parse --quiet --verify "$gitsha" > /dev/null; then
    # Get the branch containing the commit
    branch=$(git branch --contains "$gitsha" | sed 's/* //');
    echo "Found commit $gitsha in branch $branch";

    if [ branch != 'develop' ]; then
        branch = 'snapshot';
    fi

    # Set the ecr_image_tag environment variable
    ecr_image_tag="${branch}-${gitsha}"
    echo "ecr_image_tag: $ecr_image_tag"
    echo "ecr_image_tag=${ecr_image_tag}" >> $GITHUB_ENV
else
    echo "Error: Commit $gitsha not found"
fi