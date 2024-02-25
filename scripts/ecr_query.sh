repositoryName="$1"
imageTag="$2"

echo "Calling ecr query"

# Print the arguments
echo "repositoryName: $repositoryName"
echo "imageTag: $imageTag"

# Run the command and capture the output
IMAGE_META=$(aws ecr describe-images --repository-name=$repositoryName --image-ids=imageTag=$imageTag --query 'images[0]' 2>&1)
# Check if the command was successful
if [ $? -eq 0 ]; then
    # Process the output
    if [[ -n $IMAGE_META ]]; then
        IMAGE_TAG=$(echo "$IMAGE_META" | jq -r '.imageTags[0]')
        echo "Images found in repository: $repositoryName"
        echo "image_tag=$IMAGE_TAG" >> "$GITHUB_OUTPUT"
    else
        echo "No images found in repository: $repositoryName"
    fi
else
    # Command failed, check the error message
    if [[ $IMAGE_META == *"ImageNotFoundException"* ]]; then
        echo "No images found in repository: $repositoryName"
        exit 0
    else
        echo "Error: $IMAGE_META"
        exit 1
    fi
fi
echo "image_tag=$IMAGE_TAG" >> "$GITHUB_OUTPUT"