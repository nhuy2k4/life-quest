# LifeQuest Mobile - Architecture Guide

## Project Overview

LifeQuest Mobile is a React Native/Expo application built with modern best practices for iOS, Android, and web platforms.

**Technology Stack**:
- Expo 54.0.33
- React Native 0.81.5
- React 19.1.0
- TypeScript 5.9.2
- Expo Router 6.0.23 (file-based routing)
- NativeWind (Tailwind CSS)
- React Navigation 7.x

---

## 1. Folder Structure Overview

```
lifequest-mobile/
├── app/                          # File-based routing (Expo Router)
│   ├── _layout.tsx              # Root stack navigation
│   ├── modal.tsx                # Modal screen
│   └── (tabs)/                  # Route group (parentheses = grouped, not in URL)
│       ├── _layout.tsx          # Tab navigator configuration
│       ├── index.tsx            # Home screen
│       └── explore.tsx          # Explore/documentation screen
│
├── components/                   # Reusable UI components
│   ├── ui/                      # Primitive UI elements (design system)
│   │   ├── collapsible.tsx      # Expandable section component
│   │   ├── icon-symbol.ios.tsx  # iOS-specific icon symbols
│   │   └── icon-symbol.tsx      # Cross-platform icon wrapper
│   ├── external-link.tsx        # External link component
│   ├── haptic-tab.tsx           # Tab button with haptic feedback
│   ├── hello-wave.tsx           # Wave icon component
│   ├── parallax-scroll-view.tsx # Scroll view with parallax effect
│   ├── themed-text.tsx          # Theme-aware text component
│   └── themed-view.tsx          # Theme-aware container component
│
├── constants/                    # Design tokens and configuration
│   └── theme.ts                 # Colors, fonts, theme configuration
│
├── hooks/                        # Custom React hooks
│   ├── use-color-scheme.ts      # Color scheme detection
│   ├── use-color-scheme.web.ts  # Web-specific color scheme
│   └── use-theme-color.ts       # Theme color hook
│
├── assets/                       # Static assets
│   └── images/                  # Image files
│
├── scripts/                      # Build and utility scripts
│   └── reset-project.js         # Reset project to initial state
│
├── app.json                      # Expo configuration
├── babel.config.js              # Babel configuration
├── tailwind.config.js           # Tailwind CSS configuration
├── tsconfig.json                # TypeScript configuration
├── eslint.config.js             # ESLint configuration
├── package.json                 # Dependencies and scripts
└── README.md                    # Project documentation
```

### Key Pattern: Route Groups

The `(tabs)` folder uses **route groups** - a Expo Router feature where parentheses organize routes without affecting the URL structure:
- Routes inside `(tabs)` are grouped together
- The group doesn't appear in the URL path
- Allows for shared layouts (defined in `_layout.tsx`)

---

## 2. Navigation System

### Root Navigation Stack

**File**: `app/_layout.tsx`

```
RootLayout (Stack Navigation)
│
├── (tabs) ← Default anchor screen (bottom tab navigator)
│   ├── Home (app/(tabs)/index.tsx)
│   └── Explore (app/(tabs)/explore.tsx)
│
└── modal ← Modal overlay screen (stack.modal presentation)
    └── This is a modal (app/modal.tsx)
```

**Configuration Details**:

```typescript
// Root uses Stack navigation
<Stack>
  <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
  <Stack.Screen name="modal" options={{ presentation: 'modal', title: 'Modal' }} />
</Stack>
```

- `unstable_settings.anchor = '(tabs)'` makes the tabs the default entry point
- Modal uses `presentation: 'modal'` for slide-up overlay effect
- Headers are hidden on tabs, shown on modal

### Tab Navigation

**File**: `app/(tabs)/_layout.tsx`

```
TabLayout (Bottom Tab Navigator)
├── Home Tab
│   └── index.tsx
▼
└── Explore Tab
    └── explore.tsx
```

**Configuration Details**:
- Bottom tab bar with 2 tabs
- Custom `HapticTab` component for system haptic feedback on tab press
- SF Symbol icons from `@expo/vector-icons`
- Theme-aware tint colors from constants
- No header on tab screens (`headerShown: false`)

---

## 3. Screen Organization

### Tab Screens

| Screen | File Path | Purpose | Navigation Type |
|--------|-----------|---------|-----------------|
| **Home** | `app/(tabs)/index.tsx` | Main entry point, welcome message, quick start guide | Tab 1 |
| **Explore** | `app/(tabs)/explore.tsx` | Documentation, feature discovery, code examples | Tab 2 |

### Modal Screen

| Screen | File Path | Purpose | Navigation Type |
|--------|-----------|---------|-----------------|
| **Modal** | `app/modal.tsx` | Modal overlay example, demonstrates modal presentation | Stack Modal |

### Screen Navigation Flow

```
App Launch
    ↓
RootLayout (Stack)
    ↓
(tabs) [DEFAULT ANCHOR]
    ├─→ Home Screen
    │   └─→ [Tap "Explore"] ──→ Modal Screen
    │   └─→ (Back from Modal)
    │
    └─→ Explore Screen
        └─→ (Navigation back to Home)
```

### Navigation Features

- **Tab Navigation**: Swipe or tap tab bar
- **Modal Navigation**: `Link href="/modal"` triggers modal
- **Deep Linking**: Expo Router supports deep linking
- **Back Navigation**: Modal has `dismissTo` for proper back handling

---

## 4. Component Organization

### Component Structure

```
components/
├── Design System (ui/)
│   ├── icon-symbol.tsx
│   │   └── Wrapper for SF Symbols/Material Icons
│   ├── icon-symbol.ios.tsx
│   │   └── iOS-specific implementation
│   └── collapsible.tsx
│       └── Expandable accordion component
│
├── Theme Wrappers
│   ├── themed-text.tsx
│   │   └── Text component with dark/light mode support
│   └── themed-view.tsx
│       └── View container with dark/light mode support
│
└── Feature Components
    ├── parallax-scroll-view.tsx
    │   └── ScrollView with header parallax effect
    ├── haptic-tab.tsx
    │   └── Tab button with haptic feedback
    ├── external-link.tsx
    │   └── Web link wrapper component
    └── hello-wave.tsx
        └── Wave hand icon component
```

### Component Design Patterns

#### 1. Themed Components
All visual components use theme awareness:

```typescript
// themed-text.tsx
<ThemedText type="title">Heading</ThemedText>
<ThemedText type="subtitle">Subheading</ThemedText>
<ThemedText type="default">Body text</ThemedText>
<ThemedText type="defaultSemiBold">Bold text</ThemedText>
<ThemedText type="link">Link text</ThemedText>
```

#### 2. Dark Mode Support
- Uses `useColorScheme()` hook to detect system preference
- Colors defined in `constants/theme.ts`
- Automatic color switching based on device settings

#### 3. Primitive Components (ui/)
- Reusable, lower-level UI elements
- Icons, buttons, expandable sections
- Form building blocks

#### 4. Feature Components
- Composed from primitives
- Specific to feature implementations
- Can be scenario-specific

---

## 5. Constants & Theming

**File**: `constants/theme.ts`

### Color System

```typescript
Colors = {
  light: {
    text: '#11181C',
    background: '#fff',
    tint: '#0a7ea4',        // Primary brand color
    icon: '#687076',
    tabIconDefault: '#687076',
    tabIconSelected: '#0a7ea4',
  },
  dark: {
    text: '#ECEDEE',
    background: '#151718',
    tint: '#fff',
    icon: '#9BA1A6',
    tabIconDefault: '#9BA1A6',
    tabIconSelected: '#fff',
  },
}
```

### Font System

```typescript
Fonts = {
  ios: {
    sans: 'system-ui',          // Default system font
    serif: 'ui-serif',
    rounded: 'ui-rounded',      // SF Rounded (iOS 16+)
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto...",
    serif: "Georgia, 'Times New Roman', serif",
    rounded: "'SF Pro Rounded', 'Hiragino Maru Gothic ProN'...",
    mono: "monospace",
  }
}
```

### Usage in Components

```typescript
import { Colors, Fonts } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

export default function MyComponent() {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];
  
  return <Text style={{ color: colors.text }}>Text</Text>;
}
```

---

## 6. Best Practices Used

### ✅ File-Based Routing with Expo Router
- Zero configuration needed
- Intuitive file system to URL mapping
- Route groups for logical organization
- No separate routing config file
- Deep linking built-in

### ✅ TypeScript Throughout
- Full type safety
- Better IDE autocomplete
- Catch errors at compile time
- `.tsx` files for all screens and components

### ✅ Dark Mode Support
- System-wide theme detection via `useColorScheme()`
- Centralized color definitions in `constants/theme.ts`
- All UI components aware of theme
- Seamless transition on system setting change

### ✅ Design Tokens & Constants
- All colors, fonts, spacing defined in constants
- Single source of truth for styling
- Easy to maintain and update
- Consistent across the app

### ✅ Component Composition
- Reusable primitive components in `ui/` folder
- Themed wrappers around native components
- Feature components built from primitives
- Single Responsibility Principle

### ✅ Cross-Platform Support
- Works on iOS, Android, and Web
- Platform-specific implementations (e.g., `icon-symbol.ios.tsx`)
- Graceful fallbacks for unsupported features

### ✅ Accessibility Considerations
- Haptic feedback via `HapticTab` component
- Text size and contrast following standards
- Tab navigation for keyboard users
- Icons with label text alternatives

### ✅ Styling Approach
- NativeWind for utility-first styling (Tailwind CSS)
- StyleSheet for performance-critical components
- CSS-like classNames support in React Native
- Responsive design support

### ✅ Script Organization
- `reset-project.js` for easy project reset
- Pre-defined npm scripts for different platforms
- Linting configured with ESLint
- Consistent build commands

---

## 7. Extension Points for New Features

### 7.1 Adding a New Tab Screen

**Step 1**: Create the screen file
```
app/(tabs)/profile.tsx
```

**Step 2**: Implement the screen
```typescript
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';

export default function ProfileScreen() {
  return (
    <ThemedView style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <ThemedText type="title">Profile</ThemedText>
    </ThemedView>
  );
}
```

**Step 3**: Register in tab navigator
```typescript
// app/(tabs)/_layout.tsx
<Tabs.Screen
  name="profile"
  options={{
    title: 'Profile',
    tabBarIcon: ({ color }) => (
      <IconSymbol size={28} name="person.fill" color={color} />
    ),
  }}
/>
```

### 7.2 Adding a Stack Screen (Outside Tabs)

**Step 1**: Create the screen file
```
app/details.tsx
```

**Step 2**: Implement the screen
```typescript
export default function DetailsScreen() {
  return <ThemedView>{/* ... */}</ThemedView>;
}
```

**Step 3**: Register in root stack
```typescript
// app/_layout.tsx
<Stack.Screen name="details" options={{ title: 'Details' }} />
```

**Step 4**: Navigate to it
```typescript
import { Link } from 'expo-router';

<Link href="/details">
  <ThemedText type="link">Go to Details</ThemedText>
</Link>
```

### 7.3 Creating a New Modal Screen

**Step 1**: Create the modal file
```
app/settings-modal.tsx
```

**Step 2**: Implement the screen
```typescript
import { Link } from 'expo-router';

export default function SettingsModal() {
  return (
    <ThemedView style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <ThemedText type="title">Settings</ThemedText>
      <Link href="/" dismissTo>
        <ThemedText type="link">Close</ThemedText>
      </Link>
    </ThemedView>
  );
}
```

**Step 3**: Register in root stack
```typescript
// app/_layout.tsx
<Stack.Screen 
  name="settings-modal" 
  options={{ presentation: 'modal', title: 'Settings' }} 
/>
```

**Step 4**: Navigate to modal
```typescript
<Link href="/settings-modal">
  <ThemedText type="link">Open Settings</ThemedText>
</Link>
```

### 7.4 Creating Reusable UI Components

**Location**: `components/ui/[component-name].tsx`

**Example**: Creating a Button component
```typescript
// components/ui/button.tsx
import { Pressable, StyleSheet } from 'react-native';
import { ThemedText } from '../themed-text';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

interface Props {
  title: string;
  onPress: () => void;
}

export function Button({ title, onPress }: Props) {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme ?? 'light'];

  return (
    <Pressable 
      style={[styles.button, { backgroundColor: colors.tint }]}
      onPress={onPress}
    >
      <ThemedText style={{ color: 'white' }}>{title}</ThemedText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
});
```

**Usage**:
```typescript
import { Button } from '@/components/ui/button';

<Button title="Press Me" onPress={() => alert('Pressed!')} />
```

### 7.5 Adding New Theme Colors

**Update** `constants/theme.ts`:
```typescript
export const Colors = {
  light: {
    // ... existing colors
    success: '#10B981',
    error: '#EF4444',
    warning: '#F59E0B',
  },
  dark: {
    // ... existing colors
    success: '#34D399',
    error: '#F87171',
    warning: '#FBBF24',
  },
};
```

**Use in components**:
```typescript
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

const colors = Colors[useColorScheme() ?? 'light'];
return <Text style={{ color: colors.success }}>Success!</Text>;
```

### 7.6 Working with Different Screen Orientations

Expo Router automatically handles orientation changes. For custom behavior:

```typescript
import { StyleSheet, useWindowDimensions } from 'react-native';

export default function ResponsiveScreen() {
  const { width, height } = useWindowDimensions();
  const isPortrait = height > width;

  return (
    <ThemedView style={[
      styles.container,
      isPortrait ? styles.portrait : styles.landscape
    ]}>
      {/* ... */}
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  portrait: { flexDirection: 'column' },
  landscape: { flexDirection: 'row' },
});
```

---

## 8. Available Hooks

### `useColorScheme()`
Detects current color scheme preference (light/dark)

```typescript
import { useColorScheme } from '@/hooks/use-color-scheme';

const colorScheme = useColorScheme();
// Returns: 'light' | 'dark' | null | undefined
```

### `useThemeColor()`
Gets a specific theme color by name

```typescript
import { useThemeColor } from '@/hooks/use-theme-color';

const tintColor = useThemeColor('tint');
```

---

## 9. Development Commands

```bash
# Start the app
npm start

# Run on Android
npm run android

# Run on iOS
npm run ios

# Run on Web
npm run web

# Lint code
npm run lint

# Reset project
npm run reset-project
```

---

## 10. Key Files Reference

| File | Purpose |
|------|---------|
| `app/_layout.tsx` | Root navigation (Stack) |
| `app/(tabs)/_layout.tsx` | Tab navigation configuration |
| `constants/theme.ts` | Design tokens (colors, fonts) |
| `hooks/use-color-scheme.ts` | Color scheme detection |
| `components/themed-text.tsx` | Theme-aware text wrapper |
| `components/themed-view.tsx` | Theme-aware view wrapper |
| `components/ui/` | Primitive UI components |
| `tailwind.config.js` | NativeWind/Tailwind configuration |
| `tsconfig.json` | TypeScript configuration |
| `eslint.config.js` | Linting rules |

---

## 11. Troubleshooting & Common Tasks

### How to change app colors?
Update `constants/theme.ts` in the `Colors` object

### How to add a new screen?
Create a `.tsx` file in the `app/` directory and register it in `_layout.tsx`

### How to use dark mode?
All themed components automatically support dark mode. Use `useColorScheme()` to detect preference.

### How to add haptic feedback?
Use the `HapticTab` component or import from `expo-haptics`:
```typescript
import * as Haptics from 'expo-haptics';
Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
```

### How to navigate between screens?
Use the `Link` component from `expo-router`:
```typescript
import { Link } from 'expo-router';
<Link href="/screen-name"><Text>Go</Text></Link>
```

---

## Summary

This is a **modern, well-structured Expo/React Native application** that demonstrates:
- ✅ Proper file-based routing with Expo Router
- ✅ Organized folder structure with clear separation of concerns
- ✅ Comprehensive dark mode support
- ✅ Reusable component system
- ✅ Cross-platform compatibility
- ✅ TypeScript for type safety
- ✅ Scalable architecture for feature growth

The architecture is **production-ready** and can easily accommodate new features, screens, and navigation flows.
