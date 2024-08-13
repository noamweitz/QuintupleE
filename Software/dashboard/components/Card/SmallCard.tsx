import React from "react";

export default function Card({
  top,
  middle,
  bottom,
  className,
}: {
  top: React.ReactNode;
  middle: React.ReactNode;
  bottom: React.ReactNode;
  className: string;
}) {
  return (
    <div
      className={`bg-primary p-6 rounded-lg h-fit flex-auto ${className}`}
    >
      <div className="font-semibold text-[#FF8906]">
        {top}
      </div>
      <div className="font-bold text-4xl flex flex-row mt-3 mb-3">
        {middle}
      </div>
      <div className="font-semibold text-[#E53170]">
        {bottom}
      </div>
    </div>
  );
}
