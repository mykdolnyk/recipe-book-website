const recipeCardTemplate = document.getElementById("recipe-card-template")
const recipeCardList = document.getElementsByClassName("card-container")[0]
const moreBtn = document.getElementById('more-button')
const totalResults = document.getElementById('total-results')

// Parse the query params
const queryString = window.location.search;
const params = new URLSearchParams(queryString);

// Current page
let page = 1


async function getRecipes(page = 1) {
    query = `page=${page}`

    // Text
    if (params.get('text')) { query = `${query}&text=${params.get('text')}` }

    // Calories
    if (params.get('calories')) { query = `${query}&calories=${params.get('calories')}` }

    // Cooking Time
    if (params.get('minutes')) { query = `${query}&minutes=${params.get('minutes')}` }

    // Tags
    if (params.get('tags')) {
        for (let tag of params.getAll('tags')) {
            query = `${query}&recipe-tags=${tag}`
        }
    }

    // Recipe Types
    if (params.get('meal_types')) {
        for (let meal_type of params.getAll('meal_types')) {
            query = `${query}&meal-types=${meal_type}`
        }
    }

    // Custom Query Params
    if (typeof customQueryParams !== "undefined") {
        for (let [key, value] of Object.entries(customQueryParams)) {
            query = `${query}&${key}=${value}`
        }
    }

    console.log('Query Params:', query)

    let res = null
    if (typeof searchMode !== "undefined" && searchMode == true) {
        res = await fetch(`/api/recipes/search?${query}`)
    } else {
        res = await fetch(`/api/recipes?${query}`)
    }

    const data = await res.json()
    return data;
}

function renderRecipes(data) {
    console.log(data)
    recipes = data['recipe_list']

    console.log(page)

    if (data["page"] === 1) {
        if (totalResults) { totalResults.textContent = data['total'] }
    }

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
    const data = await getRecipes(page);

    if (page >= data.pages) {
        moreBtn.style.display = 'none';
    } else {
        page += 1;
    }
    renderRecipes(data);
}

loadRecipes()

if (moreBtn) {
    moreBtn.onclick = loadRecipes
}