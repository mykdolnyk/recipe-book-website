const recipeName = document.getElementById('recipe-name')
const mealType = document.getElementById('meal-type')
const tagList = document.getElementById("tag-list")
const cookingTime = document.getElementById('cooking-time')
const calories = document.getElementById('calories')
const description = document.getElementById('description')
const ingredients = document.getElementById('ingredients')
const recipeText = document.getElementById("recipe-text")

const authorLink = document.getElementById('author-link')
const authorBio = document.getElementById('author-bio')
const authorPfp = document.getElementById('author-pfp')
const likeCount = document.getElementById('like-count')


async function getRecipeData() {
    const res = await fetch(`/api/recipes/${recipeId}`)
    const data = await res.json()
    return data;
}

async function fillInRecipeData(data) {
    // Recipe 
    recipeName.textContent = data.name
    mealType.textContent = data.meal_type.name
    cookingTime.textContent = data.cooking_time
    calories.textContent = data.calories
    description.textContent = data.description
    ingredients.textContent = data.ingredients

    recipeText.innerHTML = marked.parse(data.text)
    // https://github.com/markedjs/marked

    for (let tag of data.tags) {
        let tagSpan = document.createElement("span");
        tagSpan.textContent = tag.name;
        tagList.appendChild(tagSpan);
    }

    // User
    if (authorLink) {
        authorLink.textContent = data.author.name
        authorLink.href = `/users/${data.author.id}`

        authorBio.textContent = data.author.bio
        authorPfp.src = data.author.profile_picture.path
        authorPfp.alt = `${data.name}'s Profile Picture`
        
        // todo v; and also the "add to favs" button
        likeCount.textContent = data.like_count
    }

}

data = getRecipeData().then(data => {
    fillInRecipeData(data)
})