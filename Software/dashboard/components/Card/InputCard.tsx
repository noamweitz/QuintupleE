import React from "react";
import SmallCard from "@/components/Card/SmallCard";

export default function InputCard({
  top,
  bottom,
  className,
  override,
  name,
  onKeyDown,
  value,
  onChange,
  placeholder,
}: {
  top: React.ReactNode;
  bottom: React.ReactNode;
  className?: string;
  override: boolean;
  name: string;
  onKeyDown: (e:any)=>void;
  value?: any;
  onChange?: (e: any)=>void;
  placeholder: string;
}) {
  return (
    <SmallCard
    className={`w-full ${className}`} 
    top={top}
    middle={
      <>
        <p>{name}</p>
        <input
          disabled={!override}
          placeholder={placeholder}
          onKeyDown={(e: any) => {
            if (e.key === "Enter") {
              onKeyDown(e);
            }
          }}
          value={value}
          onChange={onChange}
          className="ml-auto font-normal text-2xl outline-none border-2 rounded-md text-[#828282] pl-2 pr-2"
          type="text"
        />
      </>
    }
    bottom={bottom}
  />
  );
}
