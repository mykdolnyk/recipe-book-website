const mealTypeSelect = document.getElementById("meal-types-select")

const tagSelect = document.getElementById("tags-select")
const tagMode = document.getElementById("tags-mode")

const minCalories = document.getElementById('min-calories')
const maxCalories = document.getElementById('max-calories')

const minCookingTime = document.getElementById('min-cooking-time')
const maxCookingTime = document.getElementById('max-cooking-time')

const publicationStatus = document.getElementById('publication-status')

const sendButton = document.getElementById("send-button")

const formErrors = document.querySelector('.form-errors')
const errorList = formErrors.querySelector('ul')

document.addEventListener('DOMContentLoaded', () => {

    async function sendData() {
        mixSettings = {}

        // Meal Types
        if (mealTypeSelect.selectedOptions.length <= 0) {
            showErrors([{ "msg": 'Meal Types: Select any meal types first.' }])
            return
        }
        mixSettings.meal_type_ids = Array.from(mealTypeSelect.selectedOptions).map(option => parseInt(option.value))

        // Calories
        if (maxCalories.value) {
            mixSettings.max_calories = maxCalories.value
        }
        if (minCalories.value) {
            mixSettings.min_calories = minCalories.value
        }

        // Tags
        const tags = Array.from(tagSelect.selectedOptions).map(option => parseInt(option.value));
        if (tagMode.value == "exclude") {
            mixSettings.exclude_tags = tags
        } else {
            mixSettings.include_tags = tags
        }
        // Public/personal
        if (publicationStatus.value == 'public') {
            mixSettings.public_only = true
        } else if (publicationStatus.value == 'personal') {
            mixSettings.personal_only = true
        }

        const response = await fetch(`/api/recipe-mixes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(mixSettings)
        });

        const data = await response.json();

        if (response.ok) {
            window.location.href = `/mixes/${data.id}`;
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
 
    sendButton.onclick = sendData
});