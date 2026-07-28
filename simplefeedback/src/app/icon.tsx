import { ImageResponse } from "next/og";

export const size = {
  width: 32,
  height: 32,
};
export const contentType = "image/svg+xml";

export default function Icon() {
  return new ImageResponse(
    (
      <svg
        width="32"
        height="32"
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect width="32" height="32" rx="8" fill="#6366f1" />
        <path
          d="M8 16C8 11.5817 11.5817 8 16 8C20.4183 8 24 11.5817 24 16C24 20.4183 20.4183 24 16 24H8V16Z"
          fill="white"
          opacity="0.9"
        />
        <path
          d="M11 14H21"
          stroke="#6366f1"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <path
          d="M11 18H18"
          stroke="#6366f1"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    ),
    { ...size }
  );
}
