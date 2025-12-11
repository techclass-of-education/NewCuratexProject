const loginForm = document.querySelector('form.login');
const signupForm = document.querySelector('form.signup');
const loginBtn = document.querySelector('label.login');
const signupBtn = document.querySelector('label.signup');
const signupLink = document.querySelector('.signup-link a');
const loginText = document.querySelector('.title-text .login');
const signupText = document.querySelector('.title-text .signup');

signupBtn.onclick = (() => {
    loginForm.style.marginLeft = "-50%";
    loginText.style.marginLeft = "-50%";
});

loginBtn.onclick = (() => {
    loginForm.style.marginLeft = "0%";
    loginText.style.marginLeft = "0%";
});

signupLink.onclick = (() => {
    signupBtn.click();
    return false;
});

function toDDMMYYYY(input) {
    if (!input) return "";

    // If already dd-mm-yyyy just return
    if (/^\d{2}-\d{2}-\d{4}$/.test(input)) {
        return input;
    }

    // If format yyyy-mm-dd convert
    if (/^\d{4}-\d{2}-\d{2}$/.test(input)) {
        const [y, m, d] = input.split("-");
        return `${d}-${m}-${y}`;
    }

    // Try native Date
    const d = new Date(input);
    if (!isNaN(d.getTime())) {
        const dd = ("0" + d.getDate()).slice(2 - 2);
        const mm = ("0" + (d.getMonth() + 1)).slice(2 - 2);
        const yyyy = d.getFullYear();
        return `${dd}-${mm}-${yyyy}`;
    }

    return input; // fallback
}
