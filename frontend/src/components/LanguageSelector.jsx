
import React from "react";

function LanguageSelector({
  value = "en",
  onChange,
  languages,
}) {
  const defaultLanguages = [
    {
      code: "en",
      name: "English",
      nativeName: "English",
    },
    {
      code: "bn",
      name: "Bengali",
      nativeName: "বাংলা",
    },
    {
      code: "hi",
      name: "Hindi",
      nativeName: "हिन्दी",
    },
    {
      code: "or",
      name: "Odia",
      nativeName: "ଓଡ଼ିଆ",
    },
    {
      code: "as",
      name: "Assamese",
      nativeName: "অসমীয়া",
    },
  ];

  const availableLanguages =
    languages || defaultLanguages;

  const handleChange = (e) => {
    const selectedLanguage = e.target.value;

    if (onChange) {
      onChange(selectedLanguage);
    }
  };

  return (
    <div className="language-selector">

      <label htmlFor="language">
        🌐 Language
      </label>

      <select
        id="language"
        value={value}
        onChange={handleChange}
      >
        {availableLanguages.map(
          (language) => (
            <option
              key={language.code}
              value={language.code}
            >
              {language.nativeName}
              {" — "}
              {language.name}
            </option>
          )
        )}
      </select>

    </div>
  );
}

export default LanguageSelector;
