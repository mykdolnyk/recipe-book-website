const mealTypeSelect = document.getElementById("meal-type")
const tagSelect = document.getElementById("tag-list")

const sendButton = document.getElementById("send-button")
const deleteButton = document.getElementById("delete-button")

const publicationApplicationBlock = document.getElementById("publication-application-block")
const publishButton = document.getElementById("publish-button")
const sendApplicationButton = document.getElementById("send-application-button")

const formErrors = document.querySelector('.form-errors')
const errorList = formErrors.querySelector('ul')

document.addEventListener('DOMContentLoaded', () => {

    const simplemde = new SimpleMDE({
        element: document.getElementById("recipe-text"),
        hideIcons: ["heading"],
        showIcons: ["heading-3", "table"],
    });
    // https://github.com/sparksuite/simplemde-markdown-editor

    async function sendData() {
        const name = document.getElementById('recipe-name').value
        const cookingTime = document.getElementById('cooking-time').value
        const calories = document.getElementById('calories').value
        const description = document.getElementById('description').value
        const ingredients = document.getElementById('ingredients').value

        const mealTypeId = parseInt(mealTypeSelect.value)
        const tags = Array.from(tagSelect.selectedOptions).map(option => parseInt(option.value));

        const newData = {
            name: name,
            cooking_time: cookingTime,
            calories,
            description,
            ingredients,
            text: simplemde.value(),
            meal_type_id: mealTypeId,
            tags
        };


        const response = await fetch(`/api/recipes/${recipeId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newData)
        });

        const data = await response.json();

        if (response.ok) {
            window.location.href = `/recipes/${recipeSlug}`;
        } else {
            if (data.errors) {
                // console.log(data.errors)
                showErrors(data.errors)
            } else {
                showErrors([{ "msg": 'Unexpected error occured' }])
            }
        }

    }

    function showErrors(errors) {
        errorList.innerHTML = '';
        errors.forEach(error => {
            const li = document.createElement('li');
            
            let errorMsg
            if (error.loc && error.loc.length != 0) {
                errorMsg = `${capitalizeFirstLetter(error.loc).replace("_", " ")}: ${error.msg}`
            }
            else {
                errorMsg = `${error.msg}`
            }
            
            li.textContent = errorMsg
            errorList.appendChild(li);
        });
        formErrors.style.display = 'block';
        formErrors.style.height = 'auto';
    }
    
    
    function capitalizeFirstLetter(val) {
        return String(val).charAt(0).toUpperCase() + String(val).slice(1);
        // https://stackoverflow.com/a/1026087
    }
    
    async function sendDelete() {
        const response = await fetch(`/api/recipes/${recipeId}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            window.location.href = `/my-recipes`;
        } else {
            const data = await response.json();
            if (data.errors) {
                showErrors(data.errors)
            } else {
                showErrors([{ "msg": 'Unexpected error occured' }])
            }
        }
    }

    // --- Publication ---

    function openApplicationForm() {
        publicationApplicationBlock.style.display = "block"
        publicationApplicationBlock.style.height = "fit-content"
        publicationApplicationBlock.scrollIntoView({behavior: "smooth", block:"center"})
    }

    async function sendPublish() {
        applicationData = {
            comment: document.getElementById('application-text').value
        }

        const response = await fetch(`/api/recipes/${recipeId}/publish`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(applicationData)
        });

        if (response.ok) {
            window.location.href = `/recipes/${recipeSlug}`;
        } else {
            const data = await response.json();
            if (data.errors) {
                showErrors(data.errors)
            } else {
                showErrors([{ "msg": 'Unexpected error occured' }])
            }
        }
    }
    
    sendButton.onclick = sendData
    deleteButton.onclick = sendDelete
    publishButton.onclick = openApplicationForm
    sendApplicationButton.onclick = sendPublish
});