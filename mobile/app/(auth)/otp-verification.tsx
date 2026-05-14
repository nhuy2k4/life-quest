import { Ionicons } from '@expo/vector-icons';
import { type Href, useRouter, useLocalSearchParams } from 'expo-router';
import { useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View, Alert } from 'react-native';

import { LQButton } from '@/components/lifequest/LQButton';
import { ROUTES } from '@/constants/routes';
import { verifyEmail, resendOtp } from '@/services/authService';

export default function OtpVerificationScreen() {
  const router = useRouter();
  const { email } = useLocalSearchParams<{ email: string }>();
  
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [isVerifying, setIsVerifying] = useState(false);
  const inputRefs = useRef<(TextInput | null)[]>([]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d?$/.test(value)) return;
    const next = [...otp];
    next[index] = value;
    setOtp(next);

    if (value && index < 5) inputRefs.current[index + 1]?.focus();
  };

  const handleVerify = async () => {
    const combinedOtp = otp.join('');
    if (combinedOtp.length < 6) {
      Alert.alert('Invalid input', 'Please enter all 6 digits.');
      return;
    }
    
    if (!email) {
      Alert.alert('Missing Email', 'Target email was not forwarded.');
      return;
    }

    setIsVerifying(true);
    try {
      await verifyEmail({
        email: email,
        otp: combinedOtp
      });
      
      Alert.alert(
        'Success',
        'Email verified! Please log in to continue.',
        [{ text: 'OK', onPress: () => router.replace(ROUTES.auth.login as any) }]
      );
    } catch (err: any) {
      Alert.alert('Verification Failed', err?.message || 'Incorrect code, please try again.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResend = async () => {
    if (!email) return;
    try {
      await resendOtp({ email });
      Alert.alert('Sent', 'A new OTP code has been sent to your email.');
    } catch (err: any) {
      Alert.alert('Failed', err?.message || 'Failed to resend.');
    }
  };

  return (
    <View style={styles.container}>
      <Pressable style={styles.backButton} onPress={() => router.back()}>
        <Ionicons name="arrow-back" size={18} color="#6B7280" />
        <Text style={styles.backText}>Back</Text>
      </Pressable>

      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>Verify Your Email</Text>
          <Text style={styles.subtitle}>Enter the 6-digit code sent to {email || 'your email'}.</Text>
        </View>

        <View style={styles.otpRow}>
          {otp.map((digit, index) => (
            <TextInput
              key={`${index}`}
              ref={(ref) => {
                inputRefs.current[index] = ref;
              }}
              value={digit}
              onChangeText={(v) => handleChange(index, v)}
              style={styles.otpInput}
              keyboardType="number-pad"
              maxLength={1}
              textAlign="center"
              editable={!isVerifying}
            />
          ))}
        </View>

        <Pressable onPress={handleResend} disabled={isVerifying}>
          <Text style={styles.resend}>Resend code</Text>
        </Pressable>

        <LQButton title="Verify" variant="primary" fullWidth onPress={handleVerify} loading={isVerifying} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 52,
  },
  backButton: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 6,
    marginBottom: 24,
  },
  backText: {
    color: '#6B7280',
    fontSize: 14,
  },
  content: {
    alignSelf: 'center',
    flex: 1,
    gap: 20,
    justifyContent: 'center',
    maxWidth: 420,
    width: '100%',
  },
  header: {
    gap: 8,
  },
  title: {
    color: '#11181C',
    fontSize: 26,
    fontWeight: '700',
    textAlign: 'center',
  },
  subtitle: {
    color: '#6B7280',
    fontSize: 14,
    textAlign: 'center',
  },
  otpRow: {
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
  },
  otpInput: {
    borderColor: '#D1D5DB',
    borderRadius: 10,
    borderWidth: 1,
    fontSize: 22,
    fontWeight: '700',
    height: 56,
    width: 48,
  },
  resend: {
    color: '#6B7280',
    fontSize: 13,
    textAlign: 'center',
    textDecorationLine: 'underline',
  },
});
