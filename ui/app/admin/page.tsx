"use client";

import { useEffect, useState } from "react";
import { getUsers, getDocuments, createUser, deleteUser, addDocument, deleteDocument, updateUser } from "@/lib/api";
import { Button } from "@/components/ui/button";

const ROLES = ["Employee", "Finance", "Engineering", "Marketing", "c_level"];
const DEPARTMENTS = ["General", "Finance", "Engineering", "Marketing", "Executive"];

export default function AdminPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [docs, setDocs] = useState<any[]>([]);
  
  // New user form state
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState(ROLES[0]);
  const [newDept, setNewDept] = useState(DEPARTMENTS[0]);
  
  // New doc form state
  const [newDirName, setNewDirName] = useState("");
  const [newFiles, setNewFiles] = useState<File[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const u = await getUsers();
      setUsers(u);
      const d = await getDocuments();
      setDocs(d);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateUser = async () => {
    await createUser({ username: newUsername, password: newPassword, role: newRole, department: newDept });
    setNewUsername("");
    setNewPassword("");
    fetchData();
  };

  const handleDeleteUser = async (username: string) => {
    await deleteUser(username);
    fetchData();
  };

  const handleChangeRole = async (username: string, role: string, dept: string) => {
    await updateUser(username, { role, department: dept });
    fetchData();
  };

  const handleAddDoc = async () => {
    if (!newDirName.trim() || newFiles.length === 0) return;
    const formData = new FormData();
    formData.append("folder_name", newDirName);
    newFiles.forEach(file => {
      formData.append("files", file);
    });

    await addDocument(formData);
    setNewDirName("");
    setNewFiles([]);
    fetchData();
  };

  const handleDeleteDoc = async (id: string) => {
    await deleteDocument(id);
    fetchData();
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-12">
      <h1 className="text-3xl font-bold border-b pb-4">Admin Dashboard</h1>

      {/* Users Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">User Management</h2>
        
        <div className="flex gap-4 mb-4 border p-4 rounded bg-zinc-50 dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 items-end">
          <div>
            <label className="block text-sm font-medium">Username</label>
            <input className="border p-2 rounded w-full" value={newUsername} onChange={e => setNewUsername(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium">Password</label>
            <input type="password" className="border p-2 rounded w-full" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium">Role</label>
            <select className="border p-2 rounded" value={newRole} onChange={e => setNewRole(e.target.value)}>
              {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium">Department</label>
            <select className="border p-2 rounded" value={newDept} onChange={e => setNewDept(e.target.value)}>
              {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <Button onClick={handleCreateUser}>Create User</Button>
        </div>

        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b">
              <th className="p-2">Username</th>
              <th className="p-2">Role</th>
              <th className="p-2">Department</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.username} className="border-b">
                <td className="p-2">{u.username}</td>
                <td className="p-2">
                  <select className="border p-1 rounded" value={u.role} onChange={(e) => handleChangeRole(u.username, e.target.value, u.department)}>
                    {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </td>
                <td className="p-2">
                  <select className="border p-1 rounded" value={u.department} onChange={(e) => handleChangeRole(u.username, u.role, e.target.value)}>
                    {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </td>
                <td className="p-2">
                  <Button variant="destructive" size="sm" onClick={() => handleDeleteUser(u.username)}>Delete</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Documents Section */}
      <section className="space-y-4 pt-8">
        <h2 className="text-2xl font-semibold">Document Management (RBAC)</h2>
        
        <div className="flex gap-4 items-end mb-4 border p-4 rounded bg-zinc-50 dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Directory Name</label>
            <input 
              className="border p-2 w-full rounded" 
              value={newDirName} 
              onChange={e => setNewDirName(e.target.value)}
              placeholder="e.g. Q4_Earnings"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Files</label>
            <input 
              type="file" multiple
              className="border p-1.5 w-full rounded bg-white dark:bg-zinc-800" 
              onChange={e => {
                if(e.target.files) {
                  setNewFiles(Array.from(e.target.files));
                }
              }}
            />
          </div>
          <div>
            <Button onClick={handleAddDoc} disabled={!newDirName.trim() || newFiles.length === 0}>Upload Files</Button>
          </div>
        </div>

        <div className="space-y-4">
          {docs.map((d: any) => (
            <div key={d.id} className="border p-4 rounded shadow-sm">
              <p className="text-sm font-mono tracking-widest text-zinc-500 mb-2">FOLDER: {d.folder || 'N/A'}</p>
              <p className="font-semibold">{d.filename || 'Unknown File'}</p>
              <p className="whitespace-pre-wrap text-sm mt-2 line-clamp-3 opacity-80">{d.content}</p>
              <Button variant="destructive" size="sm" className="mt-4" onClick={() => handleDeleteDoc(d.id)}>Remove Document</Button>
            </div>
          ))}
          {docs.length === 0 && <p className="text-zinc-500 italic">No internal documents indexed.</p>}
        </div>
      </section>
    </div>
  );
}
