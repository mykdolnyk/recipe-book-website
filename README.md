# Recipe Book with Recipe Mixes - Flask Fullstack App

This is a recipe book website where users can look through and search for published recipes, create personal ones (visible only to them, or they can request their publication), and **make recipe mixes**, lifting the burden of choosing what to eat each day. That idea was the main inspiration behind this project.

The website is split into Backend and Frontend components, separating the backend and frontend concerns. The frontend is implemented via Flask’s built-in Jinja2 templates with some **vanilla JS** to query the website’s API endpoints and enhance frontend responsiveness. 

I used **Celery and its scheduler** to perform background tasks, such as calculating popular recipes, **Redis** as the broker and also for **data caching**. **PostgreSQL** is used as the DB in the **Docker Compose** setup. Also, it uses **Nginx** as a reverse proxy.

> Note: certain settings of the website are configured in a way to demonstrate its functionality (for example, scheduled tasks run much more often than it would make sense to).
> 

## Notable Features

- Markdown-supported recipe creation
- Recipe review and publication via admin panel (Flask Admin)
- Versatile built-in recipe browser
- Password protection with **bcrypt;** strong password requirements
- Custom CSRF implementation
- User profiles (with a choice of pre-set PFPs)
- Like/Favorites system (to save recipes for later and track recipe popularity)
- Popular recipes: the system finds the most relevant recipes in the last 7 days based on the amount of likes received in that time period. If there were no popular recipes, it just displays a list of recipes.
- DB fixtures
- Pytest integration

## Contents

- [Notable Features](#notable-features)
- [Contents](#contents)
- [Set Up](#set-up)
    - [Initial Set Up](#initial-set-up)
    - [Demonstration Fixtures and How to Access the Admin Panel](#demonstration-fixtures-and-how-to-access-the-admin-panel)
    - [SSL Setup](#ssl-setup)
    - [Credits](#credits)

## Set Up

### Initial Set Up

1. Clone the repository:
    
    ```bash
    git clone https://github.com/mykdolnyk/recipe-book-website.git
    cd recipe-book-website
    ```
    
2. Update the existing .ENV file (`test.env`) or create your custom one. You can also adjust different settings in the [config.py](https://github.com/mykdolnyk/recipe-book-website/blob/main/app/config.py) file.
3. Ensure that you have Docker running and start the app:
    
    ```bash
    docker compose up
    ```
    

---

### Demonstration Fixtures and How to Access the Admin Panel

This project has implemented DB fixtures to instantly add such things as Meal Types (Lunch/Dinner/etc) and Recipe Tags (Salty/Sweet, Salad/Soup, etc), but also some objects, such as demonstration Users and Recipes.

One of the User objects is an admin user that you can access to effortlessly check the website from the Admin side. Use these credentials to log into the account:

> Email: `4@example.com`
> Password: `r3pavn!f;1cFGKDS`

Once logged in, you will be able to see the “Admin Panel” button on top, which will grant you access to the admin panel.

If you don’t want to have these objects added in production, feel free to set the `LOAD_EXAMPLE_FIXTURES` variable in the [config.py](https://github.com/mykdolnyk/recipe-book-website/blob/main/app/config.py) file to `False` .

### SSL Setup

You can set up a free SSL certificate for the domain using Certbot. To do that, first you will need to make some manual changes in the existing files. In [docker-compose-ssl.yml](https://github.com/mykdolnyk/recipe-book-website/blob/main/docker-compose-ssl.yml) and [default-ssl.conf](https://github.com/mykdolnyk/recipe-book-website/blob/main/nginx/default-ssl.conf) files, change strings `%DOMAINNAME%` and `%EMAIL%` with actual domain name and email address.

Once that is done, you can run the project with:

```bash
docker compose -f docker-compose-ssl.yml up
```

Keep in mind that you still need to configure the [default-ssl.conf](https://github.com/mykdolnyk/recipe-book-website/blob/main/nginx/default-ssl.conf) file as usual to make it work with SSL. 

## Credits

I used recipes from [The Devastator’s](https://www.kaggle.com/thedevastator/datasets) [Recipes Dataset for NLP](https://www.kaggle.com/datasets/thedevastator/better-recipes-for-a-better-life) for the example recipes from DB fixtures. You can check it out here:
[https://www.kaggle.com/datasets/thedevastator/better-recipes-for-a-better-life](https://www.kaggle.com/datasets/thedevastator/better-recipes-for-a-better-life)
