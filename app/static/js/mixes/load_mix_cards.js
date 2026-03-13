const mixCardTemplate = document.getElementById("mix-card-template")
const mixCardRecipeNameTemplate = document.getElementById("mix-card-recipe-name-template")
const mixCardList = document.getElementsByClassName("mix-list-grid")[0]
const moreBtn = document.getElementById('more-button')

// Current page
let page = 1


async function getMixes(page = 1) {
    query = `page=${page}&per-page=6`

    // Custom Query Params
    if (typeof customQueryParams !== "undefined") {
        for (let [key, value] of Object.entries(customQueryParams)) {
            query = `${query}&${key}=${value}`
        }
    }

    console.log('Query Params:', query)

    const res = await fetch(`/api/recipe-mixes?${query}`)
    const data = await res.json()
    return data;
}

function renderMixes(data) {
    console.log(data)
    const mixes = data['recipe_mix_list']

    mixes.forEach(mix => {
        const mixCardClone = mixCardTemplate.content.cloneNode(true)

        mixCardClone.querySelector(".mix-date").textContent = mix.created_on
        mixCardClone.querySelector(".mix-name").textContent = mix.name
        let mixUrl = `mixes/${mix.id}`
        mixCardClone.querySelector(".mix-name").href = mixUrl

        // Recipe List:
        const mixCardRecipeList = mixCardClone.querySelector(".recipe-list")
        mix.recipes.forEach(recipe => {
            const recipeNameClone = mixCardRecipeNameTemplate.content.cloneNode(true)

            recipeNameClone.querySelector(".recipe-name").textContent = recipe.name
            let recipeUrl = `recipes/${recipe.slug}`
            recipeNameClone.querySelector(".recipe-name").href = recipeUrl

            mixCardRecipeList.appendChild(recipeNameClone)
        })

        mixCardList.appendChild(mixCardClone)
    });

}

async function loadMixes() {
    const data = await getMixes(page);

    if (page >= data.pages) {
        moreBtn.style.display = 'none';
    } else {
        page += 1;
    }
    renderMixes(data);
}

loadMixes()

if (moreBtn) {
    moreBtn.onclick = loadMixes
}