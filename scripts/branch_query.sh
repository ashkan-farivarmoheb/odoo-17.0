gitsha="$1"

echo "Calling branch query"

# Print the arguments
echo "gitsha: $gitsha"

# Fetch all branches
git fetch --all;

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