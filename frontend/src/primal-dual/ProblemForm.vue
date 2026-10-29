<script setup>
const props = defineProps({ form: { type: Object, required: true } })

const input = 'w-20 rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-center text-sm outline-none focus:border-sky-500'
const select = 'rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm outline-none focus:border-sky-500'
const btn = 'rounded-md border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800 disabled:opacity-40'

function addVar() {
  props.form.c.push('0')
  props.form.signs.push('>=0')
  props.form.cons.forEach((r) => r.a.push('0'))
}

function removeVar() {
  if (props.form.c.length <= 1) return
  props.form.c.pop()
  props.form.signs.pop()
  props.form.cons.forEach((r) => r.a.pop())
}

function addCons() {
  props.form.cons.push({ a: props.form.c.map(() => '0'), type: '<=', b: '0' })
}

function removeCons() {
  if (props.form.cons.length > 1) props.form.cons.pop()
}
</script>

<template>
  <section class="space-y-5 rounded-xl border border-slate-800 bg-slate-900/50 p-5">
    <div class="flex flex-wrap items-center gap-3">
      <label class="text-sm text-slate-400">Objetivo</label>
      <select v-model="form.sense" :class="select">
        <option value="max">Maximizar</option>
        <option value="min">Minimizar</option>
      </select>
      <div class="ml-auto flex items-center gap-2 text-sm text-slate-400">
        Variables
        <button :class="btn" :disabled="form.c.length <= 1" @click="removeVar">−</button>
        <span class="w-5 text-center text-slate-100">{{ form.c.length }}</span>
        <button :class="btn" :disabled="form.c.length >= 8" @click="addVar">+</button>
        <span class="ml-3">Restricciones</span>
        <button :class="btn" :disabled="form.cons.length <= 1" @click="removeCons">−</button>
        <span class="w-5 text-center text-slate-100">{{ form.cons.length }}</span>
        <button :class="btn" :disabled="form.cons.length >= 10" @click="addCons">+</button>
      </div>
    </div>

    <div class="overflow-x-auto">
      <div class="space-y-3">
        <div class="flex items-center gap-2">
          <span class="w-14 text-sm text-slate-400">Z =</span>
          <template v-for="(_, j) in form.c" :key="j">
            <input v-model="form.c[j]" :class="input" inputmode="decimal" />
            <span class="w-6 text-sm text-slate-400">x{{ j + 1 }}</span>
          </template>
        </div>

        <div v-for="(r, i) in form.cons" :key="i" class="flex items-center gap-2">
          <span class="w-14 text-sm text-slate-400">R{{ i + 1 }}</span>
          <template v-for="(_, j) in r.a" :key="j">
            <input v-model="r.a[j]" :class="input" inputmode="decimal" />
            <span class="w-6 text-sm text-slate-400">x{{ j + 1 }}</span>
          </template>
          <select v-model="r.type" :class="select">
            <option value="<=">≤</option>
            <option value=">=">≥</option>
            <option value="=">=</option>
          </select>
          <input v-model="r.b" :class="input" inputmode="decimal" />
        </div>

        <div class="flex items-center gap-2">
          <span class="w-14 text-sm text-slate-400">Signo</span>
          <template v-for="(_, j) in form.signs" :key="j">
            <select v-model="form.signs[j]" :class="[select, 'w-20']">
              <option value=">=0">x{{ j + 1 }} ≥ 0</option>
              <option value="<=0">x{{ j + 1 }} ≤ 0</option>
              <option value="libre">x{{ j + 1 }} libre</option>
            </select>
            <span class="w-6" />
          </template>
        </div>
      </div>
    </div>
    <p class="text-xs text-slate-500">Admite enteros, decimales y fracciones (ej: 3, 2.5, 1/3).</p>
  </section>
</template>
