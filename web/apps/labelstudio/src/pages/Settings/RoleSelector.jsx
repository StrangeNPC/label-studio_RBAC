// RBAC-feature
import { useState, useRef, useEffect } from "react";
import { Block, Elem } from "../../utils/bem";
import "./role-selector.scss";

const ROLE_OPTIONS = [
  { value: "owner", label: "Owner" },
  { value: "admin", label: "Admin" },
  { value: "manager", label: "Manager" },
  { value: "reviewer", label: "Reviewer" },
  { value: "annotator", label: "Annotator" },
  { value: "viewer", label: "Viewer" },
];

const ROLE_COLORS = {
  owner: "#8B5CF6",    // purple
  admin: "#EC4899",    // pink
  manager: "#3B82F6",  // blue
  reviewer: "#10B981", // green
  annotator: "#F59E0B", // amber
  viewer: "#6B7280",   // gray
};

export const RoleSelector = ({ currentRole, onChange, disabled, roleLabels, roleDescriptions }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);

  const currentRoleLabel = roleLabels?.[currentRole] || currentRole;
  const currentRoleColor = ROLE_COLORS[currentRole] || ROLE_COLORS.viewer;

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target)
      ) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const handleSelect = (role) => {
    if (role !== currentRole) {
      const confirmed = window.confirm(
        `Are you sure you want to change the role to ${roleLabels?.[role] || role}?`
      );

      if (confirmed) {
        onChange(role);
      }
    }
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const handleKeyDown = (e) => {
    if (disabled) return;

    switch (e.key) {
      case "Enter":
      case " ":
        e.preventDefault();
        if (isOpen && highlightedIndex >= 0) {
          handleSelect(ROLE_OPTIONS[highlightedIndex].value);
        } else {
          setIsOpen(!isOpen);
        }
        break;
      case "ArrowDown":
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex((prev) => (prev < ROLE_OPTIONS.length - 1 ? prev + 1 : 0));
        }
        break;
      case "ArrowUp":
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : ROLE_OPTIONS.length - 1));
        }
        break;
      case "Escape":
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
      default:
        break;
    }
  };

  return (
    <Block name="role-selector">
      <Elem
        name="button"
        ref={buttonRef}
        mod={{ disabled, open: isOpen }}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        tabIndex={disabled ? -1 : 0}
        role="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-disabled={disabled}
      >
        <Elem
          name="badge"
          style={{
            backgroundColor: currentRoleColor,
            color: "#fff",
          }}
        >
          {currentRoleLabel}
        </Elem>
        {!disabled && <Elem name="arrow" mod={{ up: isOpen }} />}
      </Elem>

      {isOpen && !disabled && (
        <Elem name="dropdown" ref={dropdownRef} role="listbox">
          {ROLE_OPTIONS.map((option, index) => {
            const isSelected = option.value === currentRole;
            const isHighlighted = index === highlightedIndex;
            const roleLabel = roleLabels?.[option.value] || option.label;
            const roleDescription = roleDescriptions?.[option.value];

            return (
              <Elem
                key={option.value}
                name="option"
                mod={{ selected: isSelected, highlighted: isHighlighted }}
                onClick={() => handleSelect(option.value)}
                onMouseEnter={() => setHighlightedIndex(index)}
                role="option"
                aria-selected={isSelected}
              >
                <Elem name="option-content">
                  <Elem
                    name="option-badge"
                    style={{
                      backgroundColor: ROLE_COLORS[option.value],
                      color: "#fff",
                    }}
                  >
                    {roleLabel}
                  </Elem>
                  {roleDescription && <Elem name="option-description">{roleDescription}</Elem>}
                </Elem>
                {isSelected && <Elem name="check-icon">✓</Elem>}
              </Elem>
            );
          })}
        </Elem>
      )}
    </Block>
  );
};
