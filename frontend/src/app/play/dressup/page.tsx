"use client";

import { useManneken } from "@/components/MannekenContext";
import ClothingPicker from "@/components/ClothingPicker";

export default function DressUpPage() {
  const { gender, clothes, setClothes } = useManneken();

  return (
    <>
      <h2 className="font-bold text-amber-700 text-sm mb-2">👗 Wardrobe</h2>
      <ClothingPicker gender={gender} clothes={clothes} onChange={setClothes} />
    </>
  );
}
