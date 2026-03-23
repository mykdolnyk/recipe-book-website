const recipeCardTemplate = document.getElementById("recipe-card-template")
const recipeCardList = document.getElementsByClassName("card-container")[0]

async function getPopularRecipes() {
    let res = await fetch(`/api/recipes/popular`)
    const data = await res.json()
    return data;
}

async function getRecipes() {
    let res = await fetch(`/api/recipes`)
    const data = await res.json()
    const redata = await data['recipe_list']
    return redata;
}

function renderRecipes(recipes) {
    recipes.forEach(recipe => {
        const clone = recipeCardTemplate.content.cloneNode(true)

        clone.querySelector(".meal-type").textContent = recipe.meal_type.name
        clone.querySelector(".calories").textContent = recipe.calories
        clone.querySelector(".minutes").textContent = recipe.cooking_time
        clone.querySelector(".favs").textContent = recipe.like_count
        clone.querySelector(".description").textContent = recipe.description
        clone.querySelector(".recipe-name").textContent = recipe.name

        let url = `/recipes/${recipe.slug}`
        clone.querySelector(".recipe-name").href = url

        recipeCardList.appendChild(clone)
    });

}

async function loadRecipes() {
    let data = await getPopularRecipes();
    if (data.length == 0) {
        data = await getRecipes()
        // Get all recipes
    }
    renderRecipes(data)

}

loadRecipes()
