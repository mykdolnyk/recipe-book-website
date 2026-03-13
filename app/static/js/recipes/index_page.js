const recipeCardTemplate = document.getElementById("recipe-card-template")
const recipeCardList = document.getElementsByClassName("card-container")[0]

async function getRecipes() {
    let res = await fetch(`/api/recipes/popular`)
    const data = await res.json()
    return data;
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

        recipeCardList.appendChild(clone);
    });

}

async function loadRecipes() {
    const data = await getRecipes();
    renderRecipes(data);
}

loadRecipes()
