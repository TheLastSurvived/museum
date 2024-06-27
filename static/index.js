const element1 = document.getElementById("cc-number");
const maskOptions1 = {
  mask: "0000-0000-0000-0000",
};
const mask1 = IMask(element1, maskOptions1);

const element2 = document.getElementById("cc-expiration");
const maskOptions2 = {
  mask: "00/00",
};
const mask2 = IMask(element2, maskOptions2);

const element3 = document.getElementById("cc-cvv");
const maskOptions3 = {
  mask: "000",
};
const mask3 = IMask(element3, maskOptions3);
