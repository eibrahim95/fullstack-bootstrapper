from tetra import Component, public


class Counter(Component):
    count: int = 0

    @public
    def increment(self):
        self.count += 1

    template = """
    <div class="flex items-center gap-3">
      <button class="btn-outline" @click="increment()">Count</button>
      <span data-testid="count">{{ count }}</span>
    </div>
    """
