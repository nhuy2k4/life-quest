import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { FlatList, KeyboardAvoidingView, Platform, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  createChatSocket,
  getOrCreateConversation,
  listMessages,
  markConversationRead,
  sendChatMessage,
  type ChatMessage,
} from '@/services/chatService';
import { HttpError } from '@/services/httpClient';
import { getItem, StorageKeys } from '@/utils/storage';

export default function ChatDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const initialConversationId = typeof params.conversationId === 'string' ? params.conversationId : null;
  const targetUserId = typeof params.targetUserId === 'string' ? params.targetUserId : null;
  const username = typeof params.username === 'string' ? params.username : 'Chat';
  const [conversationId, setConversationId] = useState<string | null>(initialConversationId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const sortedMessages = useMemo(
    () => [...messages].sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at)),
    [messages]
  );

  const upsertMessage = useCallback((message: ChatMessage) => {
    setMessages((prev) => {
      if (prev.some((item) => item.id === message.id)) return prev;
      return [...prev, message];
    });
  }, []);

  const loadThread = useCallback(async () => {
    setError(null);
    try {
      const token = await getItem<string>(StorageKeys.accessToken);
      if (!token) return;

      let activeConversationId = conversationId;
      if (!activeConversationId && targetUserId) {
        const conversation = await getOrCreateConversation(token, targetUserId);
        activeConversationId = conversation.id;
        setConversationId(conversation.id);
      }
      if (!activeConversationId) return;

      const response = await listMessages(token, activeConversationId);
      setMessages(response.items);
      await markConversationRead(token, activeConversationId);

      socketRef.current?.close();
      const socket = createChatSocket(token);
      socketRef.current = socket;
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type === 'message' && payload.message?.conversation_id === activeConversationId) {
          upsertMessage(payload.message);
          void markConversationRead(token, activeConversationId);
        } else if (payload.type === 'conversation_read' && payload.conversation_id === activeConversationId && payload.reader_id) {
          const readAt = new Date().toISOString();
          setMessages((prev) =>
            prev.map((item) => (item.is_mine && !item.read_at ? { ...item, read_at: readAt } : item))
          );
        }
      };
    } catch (loadError) {
      setError(loadError instanceof HttpError ? loadError.message : 'Could not open chat.');
    }
  }, [conversationId, targetUserId, upsertMessage]);

  useEffect(() => {
    void loadThread();
    return () => socketRef.current?.close();
  }, [loadThread]);

  const handleSend = async () => {
    const content = draft.trim();
    if (!content || !conversationId) return;
    setDraft('');

    const token = await getItem<string>(StorageKeys.accessToken);
    if (!token) return;

    try {
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: 'message', conversation_id: conversationId, content }));
        return;
      }
      const message = await sendChatMessage(token, conversationId, content);
      upsertMessage(message);
    } catch (sendError) {
      setDraft(content);
      setError(sendError instanceof HttpError ? sendError.message : 'Could not send message.');
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.iconButton}>
          <Ionicons name="arrow-back" size={20} color="#11181C" />
        </Pressable>
        <Text style={styles.headerTitle}>{username}</Text>
        <View style={styles.iconButton} />
      </View>

      <KeyboardAvoidingView style={styles.body} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        {error ? <Text style={styles.errorText}>{error}</Text> : null}
        <FlatList
          data={sortedMessages}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messageList}
          renderItem={({ item }) => (
            <View style={[styles.bubble, item.is_mine ? styles.mineBubble : styles.theirBubble]}>
              <Text style={[styles.bubbleText, item.is_mine ? styles.mineText : styles.theirText]}>{item.content}</Text>
              {item.is_mine && item.read_at ? <Text style={styles.readText}>Read</Text> : null}
            </View>
          )}
          ListEmptyComponent={<Text style={styles.emptyText}>Start the conversation.</Text>}
        />

        <View style={styles.inputRow}>
          <TextInput
            value={draft}
            onChangeText={setDraft}
            placeholder="Message"
            placeholderTextColor="#9CA3AF"
            multiline
            style={styles.input}
          />
          <Pressable onPress={handleSend} style={[styles.sendButton, draft.trim() ? styles.sendButtonActive : null]}>
            <Ionicons name="send" size={18} color="#fff" />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    flex: 1,
  },
  header: {
    alignItems: 'center',
    borderBottomColor: '#F3F4F6',
    borderBottomWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  iconButton: {
    alignItems: 'center',
    height: 36,
    justifyContent: 'center',
    width: 36,
  },
  headerTitle: {
    color: '#11181C',
    fontSize: 16,
    fontWeight: '700',
  },
  body: {
    flex: 1,
  },
  errorText: {
    color: '#B91C1C',
    fontSize: 13,
    padding: 12,
    textAlign: 'center',
  },
  messageList: {
    flexGrow: 1,
    gap: 8,
    justifyContent: 'flex-end',
    padding: 12,
  },
  bubble: {
    borderRadius: 16,
    maxWidth: '78%',
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  mineBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#11181C',
  },
  theirBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#F3F4F6',
  },
  bubbleText: {
    fontSize: 14,
    lineHeight: 19,
  },
  mineText: {
    color: '#fff',
  },
  theirText: {
    color: '#11181C',
  },
  readText: {
    color: '#D1D5DB',
    fontSize: 10,
    marginTop: 4,
    textAlign: 'right',
  },
  emptyText: {
    color: '#9CA3AF',
    fontSize: 14,
    textAlign: 'center',
  },
  inputRow: {
    alignItems: 'flex-end',
    borderTopColor: '#F3F4F6',
    borderTopWidth: 1,
    flexDirection: 'row',
    gap: 8,
    padding: 10,
  },
  input: {
    backgroundColor: '#F3F4F6',
    borderRadius: 18,
    color: '#11181C',
    flex: 1,
    maxHeight: 110,
    minHeight: 38,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  sendButton: {
    alignItems: 'center',
    backgroundColor: '#9CA3AF',
    borderRadius: 19,
    height: 38,
    justifyContent: 'center',
    width: 38,
  },
  sendButtonActive: {
    backgroundColor: '#11181C',
  },
});
