export type Gender = "boy" | "girl";
export type ClothingSlot = "hat" | "top" | "bottom" | "shoes";
export type Mood = "happy" | "excited" | "sad" | "angry" | "silly" | "calm" | "scared" | "curious";

export interface ClothingItem {
  id: string;
  name: string;
  emoji: string;
  colors: { primary: string; secondary: string; accent?: string };
}

export interface ClothingSelection {
  hat: string | null;
  top: string | null;
  bottom: string | null;
  shoes: string | null;
}

const SHARED_HATS: ClothingItem[] = [
  { id: "beanie", name: "Beanie", emoji: "🧶", colors: { primary: "#e53e3e", secondary: "#c53030" } },
  { id: "cap", name: "Cap", emoji: "🧢", colors: { primary: "#3182ce", secondary: "#2b6cb0" } },
  { id: "tophat", name: "Top Hat", emoji: "🎩", colors: { primary: "#1a202c", secondary: "#2d3748" } },
  { id: "crown", name: "Crown", emoji: "👑", colors: { primary: "#d69e2e", secondary: "#b7791f", accent: "#fefcbf" } },
  { id: "wizard", name: "Wizard Hat", emoji: "🧙", colors: { primary: "#6b46c1", secondary: "#553c9a", accent: "#faf089" } },
  { id: "cowboy", name: "Cowboy Hat", emoji: "🤠", colors: { primary: "#a0522d", secondary: "#8b4513" } },
  { id: "party", name: "Party Hat", emoji: "🥳", colors: { primary: "#ed64a6", secondary: "#d53f8c", accent: "#fefcbf" } },
  { id: "chef", name: "Chef Hat", emoji: "👨‍🍳", colors: { primary: "#ffffff", secondary: "#e2e8f0" } },
  { id: "helmet", name: "Helmet", emoji: "⛑️", colors: { primary: "#e53e3e", secondary: "#fc8181" } },
  { id: "pirate", name: "Pirate Hat", emoji: "🏴‍☠️", colors: { primary: "#1a202c", secondary: "#2d3748", accent: "#e53e3e" } },
];

const BOY_HATS: ClothingItem[] = [
  ...SHARED_HATS,
  { id: "detective", name: "Detective Hat", emoji: "🕵️", colors: { primary: "#4a5568", secondary: "#2d3748" } },
];

const GIRL_HATS: ClothingItem[] = [
  ...SHARED_HATS,
  { id: "tiara", name: "Tiara", emoji: "💎", colors: { primary: "#e2e8f0", secondary: "#cbd5e0", accent: "#d69e2e" } },
  { id: "flower_crown", name: "Flower Crown", emoji: "🌸", colors: { primary: "#fc8181", secondary: "#68d391", accent: "#fbb6ce" } },
];

const BOY_TOPS: ClothingItem[] = [
  { id: "tshirt_blue", name: "Blue T-Shirt", emoji: "👕", colors: { primary: "#4299e1", secondary: "#3182ce" } },
  { id: "tshirt_red", name: "Red T-Shirt", emoji: "👕", colors: { primary: "#fc8181", secondary: "#e53e3e" } },
  { id: "tshirt_green", name: "Green T-Shirt", emoji: "👕", colors: { primary: "#68d391", secondary: "#48bb78" } },
  { id: "hoodie", name: "Hoodie", emoji: "🧥", colors: { primary: "#4a5568", secondary: "#2d3748" } },
  { id: "jacket", name: "Jacket", emoji: "🧥", colors: { primary: "#2b6cb0", secondary: "#2c5282" } },
  { id: "vest", name: "Vest", emoji: "🦺", colors: { primary: "#d69e2e", secondary: "#b7791f" } },
  { id: "sweater", name: "Sweater", emoji: "🧶", colors: { primary: "#9f7aea", secondary: "#805ad5" } },
  { id: "polo", name: "Polo Shirt", emoji: "👔", colors: { primary: "#38b2ac", secondary: "#319795" } },
  { id: "tank_top", name: "Tank Top", emoji: "🎽", colors: { primary: "#ed8936", secondary: "#dd6b20" } },
  { id: "suit_jacket", name: "Suit Jacket", emoji: "🤵", colors: { primary: "#1a202c", secondary: "#2d3748", accent: "#e2e8f0" } },
  { id: "superhero", name: "Superhero Cape", emoji: "🦸", colors: { primary: "#e53e3e", secondary: "#c53030", accent: "#fefcbf" } },
];

const GIRL_TOPS: ClothingItem[] = [
  { id: "tshirt_pink", name: "Pink T-Shirt", emoji: "👕", colors: { primary: "#fbb6ce", secondary: "#ed64a6" } },
  { id: "tshirt_purple", name: "Purple T-Shirt", emoji: "👕", colors: { primary: "#d6bcfa", secondary: "#9f7aea" } },
  { id: "tshirt_yellow", name: "Yellow T-Shirt", emoji: "👕", colors: { primary: "#faf089", secondary: "#ecc94b" } },
  { id: "blouse", name: "Blouse", emoji: "👚", colors: { primary: "#bee3f8", secondary: "#90cdf4" } },
  { id: "hoodie_f", name: "Hoodie", emoji: "🧥", colors: { primary: "#fbb6ce", secondary: "#ed64a6" } },
  { id: "cardigan", name: "Cardigan", emoji: "🧶", colors: { primary: "#c6f6d5", secondary: "#9ae6b4" } },
  { id: "dress_top", name: "Crop Top", emoji: "👚", colors: { primary: "#fbd38d", secondary: "#f6ad55" } },
  { id: "sweater_f", name: "Cozy Sweater", emoji: "🧶", colors: { primary: "#e9d8fd", secondary: "#d6bcfa" } },
  { id: "tank_f", name: "Tank Top", emoji: "🎽", colors: { primary: "#fed7d7", secondary: "#fc8181" } },
  { id: "jacket_f", name: "Denim Jacket", emoji: "🧥", colors: { primary: "#63b3ed", secondary: "#4299e1" } },
  { id: "princess_top", name: "Princess Gown", emoji: "👸", colors: { primary: "#fbb6ce", secondary: "#ed64a6", accent: "#d69e2e" } },
];

const BOY_BOTTOMS: ClothingItem[] = [
  { id: "jeans", name: "Jeans", emoji: "👖", colors: { primary: "#4299e1", secondary: "#2b6cb0" } },
  { id: "shorts_blue", name: "Blue Shorts", emoji: "🩳", colors: { primary: "#63b3ed", secondary: "#4299e1" } },
  { id: "shorts_red", name: "Red Shorts", emoji: "🩳", colors: { primary: "#fc8181", secondary: "#e53e3e" } },
  { id: "cargo", name: "Cargo Pants", emoji: "👖", colors: { primary: "#a0aec0", secondary: "#718096" } },
  { id: "sweatpants", name: "Sweatpants", emoji: "👖", colors: { primary: "#4a5568", secondary: "#2d3748" } },
  { id: "chinos", name: "Chinos", emoji: "👖", colors: { primary: "#d69e2e", secondary: "#b7791f" } },
  { id: "track_pants", name: "Track Pants", emoji: "👖", colors: { primary: "#1a202c", secondary: "#e53e3e" } },
  { id: "overalls_b", name: "Overalls", emoji: "👷", colors: { primary: "#4299e1", secondary: "#2b6cb0" } },
  { id: "bermuda", name: "Bermuda Shorts", emoji: "🩳", colors: { primary: "#48bb78", secondary: "#38a169" } },
  { id: "pajama_b", name: "PJ Bottoms", emoji: "😴", colors: { primary: "#9f7aea", secondary: "#805ad5", accent: "#faf089" } },
];

const GIRL_BOTTOMS: ClothingItem[] = [
  { id: "skirt_pink", name: "Pink Skirt", emoji: "👗", colors: { primary: "#fbb6ce", secondary: "#ed64a6" } },
  { id: "skirt_blue", name: "Blue Skirt", emoji: "👗", colors: { primary: "#bee3f8", secondary: "#90cdf4" } },
  { id: "jeans_f", name: "Jeans", emoji: "👖", colors: { primary: "#4299e1", secondary: "#2b6cb0" } },
  { id: "leggings", name: "Leggings", emoji: "👖", colors: { primary: "#d6bcfa", secondary: "#b794f4" } },
  { id: "tutu", name: "Tutu", emoji: "🩰", colors: { primary: "#fbb6ce", secondary: "#fce4ec" } },
  { id: "shorts_f", name: "Shorts", emoji: "🩳", colors: { primary: "#fbd38d", secondary: "#f6ad55" } },
  { id: "overalls_f", name: "Overalls", emoji: "👷", colors: { primary: "#fc8181", secondary: "#e53e3e" } },
  { id: "long_skirt", name: "Long Skirt", emoji: "👗", colors: { primary: "#c6f6d5", secondary: "#9ae6b4" } },
  { id: "plaid_skirt", name: "Plaid Skirt", emoji: "👗", colors: { primary: "#e53e3e", secondary: "#1a202c" } },
  { id: "pajama_f", name: "PJ Bottoms", emoji: "😴", colors: { primary: "#fbb6ce", secondary: "#fed7d7", accent: "#fc8181" } },
];

const BOY_SHOES: ClothingItem[] = [
  { id: "sneakers_w", name: "White Sneakers", emoji: "👟", colors: { primary: "#e2e8f0", secondary: "#cbd5e0" } },
  { id: "sneakers_r", name: "Red Sneakers", emoji: "👟", colors: { primary: "#e53e3e", secondary: "#c53030" } },
  { id: "sneakers_b", name: "Blue Sneakers", emoji: "👟", colors: { primary: "#3182ce", secondary: "#2b6cb0" } },
  { id: "boots", name: "Boots", emoji: "🥾", colors: { primary: "#744210", secondary: "#5a3e1a" } },
  { id: "sandals_b", name: "Sandals", emoji: "🩴", colors: { primary: "#a0522d", secondary: "#8b4513" } },
  { id: "rain_boots", name: "Rain Boots", emoji: "🌧️", colors: { primary: "#ecc94b", secondary: "#d69e2e" } },
  { id: "soccer", name: "Soccer Cleats", emoji: "⚽", colors: { primary: "#1a202c", secondary: "#48bb78" } },
  { id: "slippers_b", name: "Slippers", emoji: "🧸", colors: { primary: "#a0aec0", secondary: "#718096" } },
  { id: "hightops", name: "High-Tops", emoji: "👟", colors: { primary: "#1a202c", secondary: "#e53e3e" } },
  { id: "crocs_b", name: "Crocs", emoji: "🐊", colors: { primary: "#48bb78", secondary: "#38a169" } },
];

const GIRL_SHOES: ClothingItem[] = [
  { id: "sneakers_pink", name: "Pink Sneakers", emoji: "👟", colors: { primary: "#ed64a6", secondary: "#d53f8c" } },
  { id: "sneakers_wf", name: "White Sneakers", emoji: "👟", colors: { primary: "#e2e8f0", secondary: "#fbb6ce" } },
  { id: "ballet", name: "Ballet Flats", emoji: "🩰", colors: { primary: "#fbb6ce", secondary: "#ed64a6" } },
  { id: "mary_jane", name: "Mary Janes", emoji: "👞", colors: { primary: "#1a202c", secondary: "#2d3748" } },
  { id: "sandals_f", name: "Sandals", emoji: "🩴", colors: { primary: "#d69e2e", secondary: "#b7791f" } },
  { id: "rain_boots_f", name: "Rain Boots", emoji: "🌧️", colors: { primary: "#ed64a6", secondary: "#d53f8c" } },
  { id: "ugg", name: "Fuzzy Boots", emoji: "🥾", colors: { primary: "#d2b48c", secondary: "#c4a882" } },
  { id: "slippers_f", name: "Bunny Slippers", emoji: "🐰", colors: { primary: "#fbb6ce", secondary: "#fed7d7" } },
  { id: "sparkle", name: "Sparkle Shoes", emoji: "✨", colors: { primary: "#d69e2e", secondary: "#ecc94b", accent: "#fefcbf" } },
  { id: "crocs_f", name: "Crocs", emoji: "🐊", colors: { primary: "#9f7aea", secondary: "#805ad5" } },
];

export function getClothingOptions(gender: Gender, slot: ClothingSlot): ClothingItem[] {
  const catalog = {
    boy: { hat: BOY_HATS, top: BOY_TOPS, bottom: BOY_BOTTOMS, shoes: BOY_SHOES },
    girl: { hat: GIRL_HATS, top: GIRL_TOPS, bottom: GIRL_BOTTOMS, shoes: GIRL_SHOES },
  };
  return catalog[gender][slot];
}

export function getClothingItem(gender: Gender, slot: ClothingSlot, id: string): ClothingItem | undefined {
  return getClothingOptions(gender, slot).find((item) => item.id === id);
}

export const MOOD_CONFIG: Record<Mood, { emoji: string; label: string; bg: string; accent: string }> = {
  happy: { emoji: "😊", label: "Happy", bg: "bg-yellow-50", accent: "border-yellow-300" },
  excited: { emoji: "🤩", label: "Excited", bg: "bg-orange-50", accent: "border-orange-300" },
  sad: { emoji: "😢", label: "Sad", bg: "bg-blue-50", accent: "border-blue-300" },
  angry: { emoji: "😤", label: "Grumpy", bg: "bg-red-50", accent: "border-red-300" },
  silly: { emoji: "🤪", label: "Silly", bg: "bg-purple-50", accent: "border-purple-300" },
  calm: { emoji: "😌", label: "Calm", bg: "bg-green-50", accent: "border-green-300" },
  scared: { emoji: "😨", label: "Scared", bg: "bg-gray-50", accent: "border-gray-400" },
  curious: { emoji: "🧐", label: "Curious", bg: "bg-teal-50", accent: "border-teal-300" },
};