const loginForm = document.querySelector('form.login');
const signupForm = document.querySelector('form.signup');
const loginBtn = document.querySelector('label.login');
const signupBtn = document.querySelector('label.signup');
const signupLink = document.querySelector('.signup-link a');
const loginText = document.querySelector('.title-text .login');
const signupText = document.querySelector('.title-text .signup');


if(signupBtn)
{
signupBtn.onclick = (() => {
    loginForm.style.marginLeft = "-50%";
    loginText.style.marginLeft = "-50%";
});
}

if(loginBtn)
{
loginBtn.onclick = (() => {
    loginForm.style.marginLeft = "0%";
    loginText.style.marginLeft = "0%";
});
}

if(signupLink)
{
signupLink.onclick = (() => {
    signupBtn.click();
    return false;
});
}
