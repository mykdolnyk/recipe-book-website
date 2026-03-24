const usernamePlaces = document.getElementsByClassName('user-name')
const bio = document.getElementById('bio')
const pfp = document.getElementById('pfp')

const recipeCount = document.getElementById('recipe-count')
const likeCount = document.getElementById('like-count')

async function getUserData() {
    const res = await fetch(`/api/users/${userId}`)
    const data = await res.json()
    return data;
}

async function fillInUserData(data) {
    // UN
    for (let place of usernamePlaces) {
        place.textContent = data.name
    }
    // Other
    bio.textContent = data.bio
    pfp.src = data.profile_picture.path
    pfp.alt = `${data.name}'s Profile Picture`
    recipeCount.textContent = data.recipe_count
    likeCount.textContent = data.like_count
}

data = getUserData().then(data => {
    console.log(data)
    fillInUserData(data)
})