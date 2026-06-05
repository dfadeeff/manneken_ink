"use client";

import { Gender, ClothingSlot, ClothingSelection, getClothingOptions } from "./clothingData";

const SLOT_INFO: { key: ClothingSlot; label: string; emoji: string }[] = [
  { key: "hat", label: "Hats", emoji: "🎩" },
  { key: "top", label: "Tops", emoji: "👕" },
  { key: "bottom", label: "Bottoms", emoji: "👖" },
  { key: "shoes", label: "Shoes", emoji: "👟" },
];

interface Props {
  gender: Gender;
  clothes: ClothingSelection;
  onChange: (clothes: ClothingSelection) => void;
}

export default function ClothingPicker({ gender, clothes, onChange }: Props) {
  function select(slot: ClothingSlot, id: string | null) {
    onChange({ ...clothes, [slot]: clothes[slot] === id ? null : id });
  }

  return (
    <div className="space-y-3">
      {SLOT_INFO.map((slot) => {
        const options = getClothingOptions(gender, slot.key);
        return (
          <div key={slot.key}>
            <h3 className="text-xs font-bold text-amber-700 mb-1">
              {slot.emoji} {slot.label}
            </h3>
            <div className="flex gap-1.5 overflow-x-auto pb-1">
              <button
                onClick={() => select(slot.key, null)}
                className={`shrink-0 px-2 py-1 rounded-lg text-xs transition-all ${
                  clothes[slot.key] === null
                    ? "bg-gray-200 ring-2 ring-amber-400 font-bold"
                    : "bg-gray-100 hover:bg-gray-200"
                }`}
              >
                ❌ None
              </button>
              {options.map((item) => (
                <button
                  key={item.id}
                  onClick={() => select(slot.key, item.id)}
                  className={`shrink-0 px-2 py-1 rounded-lg text-xs transition-all flex items-center gap-1 ${
                    clothes[slot.key] === item.id
                      ? "ring-2 ring-amber-400 font-bold shadow-sm"
                      : "hover:shadow-sm"
                  }`}
                  style={{
                    backgroundColor: item.colors.primary + "30",
                    borderLeft: `3px solid ${item.colors.primary}`,
                  }}
                >
                  <span>{item.emoji}</span>
                  <span className="whitespace-nowrap">{item.name}</span>
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}