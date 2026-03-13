const likeButton = document.getElementById('like-button')
// const likeCount = document.getElementById('like-count')

async function wasRecipeLiked() {
    const res = await fetch(`/api/recipes/${recipeId}/like`)
    const data = await res.json()
    return data.liked;
}

async function likeRecipe() {
    await fetch(`/api/recipes/${recipeId}/like`, {
        method: 'POST'
    })
}

async function unLikeRecipe() {
    await fetch(`/api/recipes/${recipeId}/like`, {
        method: 'DELETE'
    })
}

async function updateLikeButtonAppearance(liked) {
    if (liked) {
        likeButton.textContent = "Unlike"
    } else {
        likeButton.textContent = "Like"
    }
}

async function updateLikeCount(liked) {
    let currentLikeCount = parseInt(likeCount.textContent)
    if (liked) {
        likeCount.textContent = currentLikeCount + 1
    } else {
        likeCount.textContent = currentLikeCount - 1
    }
}

async function processButtonClick() {
    let liked = await wasRecipeLiked()
    console.log(liked)

    if (liked === true) {
        unLikeRecipe()
    } else if (liked === false) {
        likeRecipe()
    }

    updateLikeButtonAppearance(!liked)
    updateLikeCount(!liked)
}

(async () => {
    let liked = await wasRecipeLiked()
    console.log(liked)
    updateLikeButtonAppearance(liked)
})();

likeButton.onclick = processButtonClick