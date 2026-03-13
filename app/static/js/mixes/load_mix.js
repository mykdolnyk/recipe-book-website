const mixName = document.getElementById('mix-name')
const recipeCardTemplate = document.getElementById('recipe-card-template')


async function getMixData() {
    const res = await fetch(`/api/recipe-mixes/${mixId}`)
    const data = await res.json()
    return data;
}

async function fillInMixData(data) {
    mixName.textContent = data.name
    renderRecipes(data.recipes)
}

function renderRecipes(recipeList) {
    console.log(recipeList)

    recipeList.forEach(recipe => {
        const clone = recipeCardTemplate.content.cloneNode(true)

        clone.querySelector(".meal-type").textContent = recipe.meal_type.name
        clone.querySelector(".calories").textContent = recipe.calories
        clone.querySelector(".minutes").textContent = recipe.cooking_time
        clone.querySelector(".description").textContent = recipe.description
        clone.querySelector(".recipe-name").textContent = recipe.name

        let url = `/recipes/${recipe.slug}`
        clone.querySelector(".recipe-name").href = url

        document.getElementsByTagName('main')[0].appendChild(clone);
    });

}


data = getMixData().then(data => {
    fillInMixData(data)
})