const mealTypesSelect = document.getElementById("meal-types-select");
const tagsSelect = document.getElementById("tags-select");
const form = document.getElementById("search-bar")
const searchMode = true

async function getMealTypes() {
    const res = await fetch(`/api/meal-types`)
    const data = await res.json()
    return data['meal_type_list']
}
function renderMealTypes(meal_type_list) {
    meal_type_list.forEach(meal_type => {
        let option = document.createElement('option')
        option.value = meal_type.id
        option.text = meal_type.name
        mealTypesSelect.appendChild(option)
    });

}

async function getTags() {
    const res = await fetch(`/api/recipe-tags`)
    const data = await res.json()
    return data['recipe_tag_list']
}
function renderTags(tag_list) {
    tag_list.forEach(tag => {
        let option = document.createElement('option')
        option.value = tag.id
        option.text = tag.name
        tagsSelect.appendChild(option)
    });

}

function fillInParams() {
    const queryString = window.location.search;
    const params = new URLSearchParams(queryString)

    for (const [name, value] of params.entries()) {
        const field = form.elements[name]
        field.value = value
    }
}

getMealTypes().then(meal_type_list => {
    renderMealTypes(meal_type_list)
})

getTags().then(tag_list => {
    renderTags(tag_list)
})


fillInParams()