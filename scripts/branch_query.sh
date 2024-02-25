gitsha="$1"

echo "Calling branch query"

# Print the arguments
echo "gitsha: $gitsha"

git fetch --all
branch=$(git branch --contains $gitsha  | sed 's/* //')
echo "ecr_image_tag: $branch-$gitsha"
echo "ecr_image_tag=${branch}-$gitsha" >> $GITHUB_ENV